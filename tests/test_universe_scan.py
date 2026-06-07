"""Tests for UniverseScreenerAgent, QuarterlyEarningsAgent, UniverseScanOrchestrator, JobStore."""
import json
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch, call

import pytest

from src.agents.universe_screener import UniverseScreenerAgent, NIFTY100_FALLBACK
from src.agents.quarterly_earnings import QuarterlyEarningsAgent
from src.agents.universe_scan import UniverseScanOrchestrator, _score_lynch, _pick_top10
from src.api import job_store


# -----------------------------------------------------------------------
# Shared config fixture
# -----------------------------------------------------------------------

@dataclass
class FakeLLM:
    anthropic_api_key: Optional[str] = None
    model: str = "claude-opus-4-8"
    max_tokens: int = 8192


@dataclass
class FakeCfg:
    llm: FakeLLM = field(default_factory=FakeLLM)
    news_api_key: Optional[str] = None
    paper_trading: bool = True
    log_level: str = "INFO"


def make_cfg():
    return FakeCfg()


# -----------------------------------------------------------------------
# Fake yfinance info dict
# -----------------------------------------------------------------------

def fake_yf_info(ticker="RELIANCE", mcap=1_930_000_00_00_000, rev=997_025_00_00_000):
    return {
        "regularMarketPrice": 2850.0,
        "marketCap": mcap,
        "totalRevenue": rev,
        "freeCashflow": 45_000_00_00_000,
        "totalDebt": 312_000_00_00_000,
        "totalCash": 180_000_00_00_000,
        "returnOnEquity": 0.185,
        "returnOnAssets": 0.08,
        "debtToEquity": 42.0,
        "trailingPE": 29.7,
        "priceToBook": 3.35,
        "pegRatio": 1.2,
        "trailingEps": 96.0,
        "bookValue": 850.0,
        "dividendYield": 0.0035,
        "revenueGrowth": 0.15,
        "earningsGrowth": 0.12,
        "grossMargins": 0.35,
        "operatingMargins": 0.18,
        "profitMargins": 0.10,
        "currentRatio": 1.4,
        "ebitda": 160_000_00_00_000,
        "sharesOutstanding": 677_00_00_000,
        "longBusinessSummary": "Reliance Industries is India's largest conglomerate.",
        "longName": "Reliance Industries Limited",
        "sector": "Energy",
        "industry": "Oil & Gas Refining & Marketing",
        "fiftyTwoWeekHigh": 3100.0,
        "fiftyTwoWeekLow": 2200.0,
        "beta": 0.9,
    }


def fake_small_cap_info():
    return {
        "regularMarketPrice": 1200.0,
        "marketCap": 2_500_00_00_000,      # ₹2500 Cr
        "totalRevenue": 800_00_00_000,       # ₹800 Cr
        "freeCashflow": 100_00_00_000,
        "totalDebt": 50_00_00_000,
        "totalCash": 200_00_00_000,
        "returnOnEquity": 0.25,
        "debtToEquity": 6.0,               # low D/E (yfinance reports as %)
        "trailingPE": 22.0,
        "priceToBook": 4.0,
        "pegRatio": 0.8,
        "trailingEps": 55.0,
        "bookValue": 300.0,
        "dividendYield": 0.01,
        "revenueGrowth": 0.45,
        "earningsGrowth": 0.50,
        "grossMargins": 0.40,
        "operatingMargins": 0.22,
        "profitMargins": 0.15,
        "ebitda": 175_00_00_000,
        "sharesOutstanding": 2_08_00_000,
        "longBusinessSummary": "Small defense drone company with AI capabilities.",
        "longName": "SmallDefense Ltd",
        "sector": "Industrials",
        "industry": "Aerospace & Defense",
        "beta": 1.2,
    }


# -----------------------------------------------------------------------
# UniverseScreenerAgent tests
# -----------------------------------------------------------------------

class TestUniverseScreenerAgent:

    def test_parse_info_converts_units_correctly(self):
        agent = UniverseScreenerAgent(config=make_cfg())
        info = fake_yf_info()
        parsed = agent._parse_info("RELIANCE", info)

        assert parsed["ticker"] == "RELIANCE"
        assert parsed["current_price"] == 2850.0
        assert parsed["market_cap_cr"] == pytest.approx(1930000, rel=0.01)
        assert parsed["roe"] == pytest.approx(0.185)
        assert parsed["sector"] == "Energy"
        assert "Reliance" in parsed["business_description"]

    def test_prefilter_passes_good_stock(self):
        agent = UniverseScreenerAgent(config=make_cfg())
        stock = agent._parse_info("RELIANCE", fake_yf_info())
        passes, reason = agent._passes_prefilter(stock)
        assert passes, reason

    def test_prefilter_rejects_micro_cap(self):
        agent = UniverseScreenerAgent(config=make_cfg())
        info = fake_yf_info(mcap=50_00_00_000)  # ₹50 Cr
        stock = agent._parse_info("TINYCORP", info)
        passes, reason = agent._passes_prefilter(stock)
        assert not passes
        assert "market_cap" in reason

    def test_prefilter_rejects_penny_stock(self):
        agent = UniverseScreenerAgent(config=make_cfg())
        info = {**fake_yf_info(), "regularMarketPrice": 3.0}
        stock = agent._parse_info("PENNY", info)
        passes, reason = agent._passes_prefilter(stock)
        assert not passes
        assert "price" in reason

    def test_prefilter_rejects_no_revenue(self):
        agent = UniverseScreenerAgent(config=make_cfg())
        info = fake_yf_info(rev=0)
        stock = agent._parse_info("NOREV", info)
        passes, reason = agent._passes_prefilter(stock)
        assert not passes

    def test_prefilter_rejects_bad_roe(self):
        agent = UniverseScreenerAgent(config=make_cfg())
        info = {**fake_yf_info(), "returnOnEquity": 0.02}
        stock = agent._parse_info("BADROE", info)
        passes, reason = agent._passes_prefilter(stock)
        assert not passes
        assert "roe" in reason

    def test_prefilter_high_de_financial_sector_exempt(self):
        """Banks have high D/E naturally — they should not be filtered on D/E alone."""
        agent = UniverseScreenerAgent(config=make_cfg())
        # yfinance reports D/E as %, so 600 = 6.0 ratio; after /100 = 6.0, limit = 4.0*3 = 12.0
        info = {**fake_yf_info(), "debtToEquity": 600.0, "sector": "Financial Services",
                "returnOnEquity": 0.15}
        stock = agent._parse_info("HDFC", info)
        # Financial sector gets 3x D/E allowance (6.0 < 12.0)
        passes, reason = agent._passes_prefilter(stock)
        assert passes

    def test_quant_score_high_quality_stock(self):
        agent = UniverseScreenerAgent(config=make_cfg())
        stock = {
            "roe": 0.25, "debt_equity": 0.3, "revenue_growth_yoy": 0.20,
            "earnings_growth_yoy": 0.25, "peg_ratio": 0.8, "profit_margin": 0.18,
            "operating_margin": 0.22, "fcf_cr": 5000, "market_cap_cr": 10000,
            "dividend_yield": 0.03, "beta": 0.9,
        }
        scores = agent._quant_score(stock)
        assert scores["buffett_quant_score"] >= 7.0
        assert scores["lynch_quant_score"] >= 6.0
        assert scores["composite_screen_score"] >= 7.0

    def test_quant_score_risky_stock(self):
        agent = UniverseScreenerAgent(config=make_cfg())
        stock = {
            "roe": 0.05, "debt_equity": 3.5, "revenue_growth_yoy": -0.05,
            "earnings_growth_yoy": -0.10, "peg_ratio": 5.0, "profit_margin": 0.01,
            "operating_margin": 0.02, "fcf_cr": -500, "market_cap_cr": 50000,
            "dividend_yield": 0.0, "beta": 2.0,
        }
        scores = agent._quant_score(stock)
        assert scores["risk_quant_score"] >= 4.0
        assert scores["composite_screen_score"] < 5.0

    def test_screen_with_mocked_fetch(self):
        agent = UniverseScreenerAgent(config=make_cfg(), max_stocks=3)

        def mock_fetch(symbol):
            return fake_yf_info() if symbol != "BADSTOCK" else None

        with patch.object(agent, "_fetch_stock_info", side_effect=mock_fetch):
            with patch.object(agent, "get_symbol_list", return_value=["RELIANCE", "TCS", "BADSTOCK"]):
                result = agent.screen(top_n=10)

        assert result["total_symbols_scanned"] == 3
        assert result["fetch_failures"] >= 1
        assert "candidates" in result
        assert len(result["candidates"]) >= 1

    def test_screen_all_fetch_failures(self):
        agent = UniverseScreenerAgent(config=make_cfg())
        with patch.object(agent, "_fetch_stock_info", return_value=None):
            with patch.object(agent, "get_symbol_list", return_value=["A", "B"]):
                result = agent.screen(top_n=10)
        assert result["candidates"] == []
        assert result["fetch_failures"] == 2

    def test_screen_progress_callback(self):
        agent = UniverseScreenerAgent(config=make_cfg())
        calls = []

        def cb(done, total):
            calls.append((done, total))

        with patch.object(agent, "_fetch_stock_info", return_value=fake_yf_info()):
            with patch.object(agent, "get_symbol_list", return_value=["TCS"]):
                agent.screen(top_n=5, progress_callback=cb)

        assert len(calls) > 0

    def test_get_symbol_list_fallback(self):
        agent = UniverseScreenerAgent(config=make_cfg())
        with patch("src.agents.data_collector.DataCollectorAgent.fetch_nse_stock_list",
                   side_effect=Exception("API down")):
            symbols = agent.get_symbol_list()
        assert len(symbols) > 0
        assert "RELIANCE" in symbols

    def test_nifty100_fallback_not_empty(self):
        assert len(NIFTY100_FALLBACK) >= 50
        assert all(isinstance(s, str) for s in NIFTY100_FALLBACK)

    def test_parse_info_missing_fields_handled(self):
        agent = UniverseScreenerAgent(config=make_cfg())
        minimal_info = {"regularMarketPrice": 100.0, "marketCap": 1000_00_00_000,
                        "totalRevenue": 500_00_00_000}
        parsed = agent._parse_info("MIN", minimal_info)
        assert parsed["roe"] is None
        assert parsed["peg_ratio"] is None
        assert parsed["business_description"] == ""

    def test_candidates_sorted_by_composite_score(self):
        agent = UniverseScreenerAgent(config=make_cfg())
        good = {**agent._parse_info("GOOD", fake_yf_info()),
                **agent._quant_score({"roe": 0.25, "debt_equity": 0.2, "revenue_growth_yoy": 0.30,
                                       "earnings_growth_yoy": 0.35, "peg_ratio": 0.7, "profit_margin": 0.20,
                                       "operating_margin": 0.25, "fcf_cr": 1000, "market_cap_cr": 5000,
                                       "dividend_yield": 0.03, "beta": 0.8})}
        bad = {**agent._parse_info("BAD", fake_yf_info()),
               **agent._quant_score({"roe": 0.07, "debt_equity": 2.5, "revenue_growth_yoy": 0.02,
                                      "earnings_growth_yoy": 0.01, "peg_ratio": 4.0, "profit_margin": 0.02,
                                      "operating_margin": 0.03, "fcf_cr": -100, "market_cap_cr": 50000,
                                      "dividend_yield": 0.0, "beta": 1.8})}
        assert good["composite_screen_score"] > bad["composite_screen_score"]


# -----------------------------------------------------------------------
# QuarterlyEarningsAgent tests
# -----------------------------------------------------------------------

class TestQuarterlyEarningsAgent:

    def _make_mock_df(self, num_quarters=4):
        """Build a minimal mock DataFrame-like object."""
        import pandas as pd
        import numpy as np
        dates = pd.date_range("2024-09-30", periods=num_quarters, freq="-3ME")
        data = {
            "Total Revenue": [900e9, 850e9, 800e9, 750e9][:num_quarters],
            "Gross Profit": [315e9, 297e9, 280e9, 262e9][:num_quarters],
            "EBIT": [162e9, 153e9, 144e9, 135e9][:num_quarters],
            "Net Income": [80e9, 75e9, 70e9, 65e9][:num_quarters],
        }
        return pd.DataFrame(data, index=list(data.keys()), columns=dates)

    def _make_cf_df(self, num_quarters=4):
        import pandas as pd
        dates = pd.date_range("2024-09-30", periods=num_quarters, freq="-3ME")
        data = {"Operating Cash Flow": [90e9, 85e9, 80e9, 75e9][:num_quarters]}
        return pd.DataFrame(data, index=list(data.keys()), columns=dates)

    def test_analyze_with_mock_data(self):
        agent = QuarterlyEarningsAgent()
        mock_raw = {
            "financials": self._make_mock_df(),
            "cashflow": self._make_cf_df(),
        }
        with patch.object(agent, "_fetch_quarterly_data", return_value=mock_raw):
            result = agent.analyze("RELIANCE")

        assert result["ticker"] == "RELIANCE"
        assert 0 <= result["earnings_quality_score"] <= 10
        assert len(result["quarters"]) <= 4
        assert "trends" in result

    def test_analyze_returns_error_on_fetch_failure(self):
        agent = QuarterlyEarningsAgent()
        with patch.object(agent, "_fetch_quarterly_data", return_value={}):
            result = agent.analyze("FAIL")

        assert result["ticker"] == "FAIL"
        assert "error" in result
        assert result["earnings_quality_score"] == 5.0

    def test_analyze_empty_dataframe(self):
        import pandas as pd
        agent = QuarterlyEarningsAgent()
        mock_raw = {"financials": pd.DataFrame(), "cashflow": pd.DataFrame()}
        with patch.object(agent, "_fetch_quarterly_data", return_value=mock_raw):
            result = agent.analyze("EMPTY")
        assert "error" in result

    def test_pct_change_calculation(self):
        agent = QuarterlyEarningsAgent()
        assert agent._pct_change(110, 100) == pytest.approx(0.10, rel=0.01)
        assert agent._pct_change(90, 100) == pytest.approx(-0.10, rel=0.01)
        assert agent._pct_change(None, 100) is None
        assert agent._pct_change(100, 0) is None

    def test_earnings_quality_score_strong_growth(self):
        agent = QuarterlyEarningsAgent()
        trends = {
            "revenue_yoy_growth": 0.30,
            "profit_yoy_growth": 0.35,
            "margin_expanding": True,
            "earnings_accelerating": True,
            "earnings_consistency_pct": 1.0,
            "quarters_with_positive_fcf": 4,
            "total_quarters_analysed": 4,
        }
        score = agent._earnings_quality_score(trends, [])
        assert score >= 7.0

    def test_earnings_quality_score_declining(self):
        agent = QuarterlyEarningsAgent()
        trends = {
            "revenue_yoy_growth": -0.10,
            "profit_yoy_growth": -0.15,
            "margin_expanding": False,
            "earnings_accelerating": False,
            "earnings_consistency_pct": 0.40,
            "quarters_with_positive_fcf": 1,
            "total_quarters_analysed": 4,
        }
        score = agent._earnings_quality_score(trends, [])
        assert score <= 4.0

    def test_compute_trends_insufficient_data(self):
        agent = QuarterlyEarningsAgent()
        result = agent._compute_trends([{"revenue_cr": 100}])
        assert result["trend"] == "insufficient_data"

    def test_compute_trends_yoy(self):
        agent = QuarterlyEarningsAgent()
        quarters = [
            {"revenue_cr": 120, "net_income_cr": 24, "net_margin": 0.20},  # Q current
            {"revenue_cr": 110, "net_income_cr": 22, "net_margin": 0.20},  # Q-1
            {"revenue_cr": 105, "net_income_cr": 20, "net_margin": 0.19},  # Q-2
            {"revenue_cr": 100, "net_income_cr": 18, "net_margin": 0.18},  # Q-3
            {"revenue_cr": 100, "net_income_cr": 20, "net_margin": 0.20},  # Q-4 (same qtr last year)
        ]
        trends = agent._compute_trends(quarters)
        assert trends["revenue_yoy_growth"] == pytest.approx(0.20, rel=0.01)

    def test_safe_cr_returns_none_on_bad_df(self):
        agent = QuarterlyEarningsAgent()
        result = agent._safe_cr(None, "Total Revenue", 0)
        assert result is None


# -----------------------------------------------------------------------
# UniverseScanOrchestrator tests
# -----------------------------------------------------------------------

class TestUniverseScanOrchestrator:

    MOCK_SCREEN_RESULT = {
        "total_symbols_scanned": 100,
        "passed_prefilter": 20,
        "fetch_failures": 5,
        "rejected_by_filter": 75,
        "candidates_returned": 3,
        "candidates": [
            {
                "ticker": "RELIANCE",
                "name": "Reliance Industries",
                "sector": "Energy",
                "industry": "Oil & Gas",
                "current_price": 2850.0,
                "market_cap_cr": 1930000,
                "fcf_cr": 45000,
                "debt_cr": 312000,
                "cash_cr": 180000,
                "ebitda_cr": 160000,
                "eps": 96.0,
                "book_value_per_share": 850.0,
                "shares_outstanding_cr": 677.0,
                "business_description": "Reliance Industries is India's largest conglomerate.",
                "buffett_quant_score": 7.5,
                "lynch_quant_score": 6.0,
                "composite_screen_score": 7.2,
            },
            {
                "ticker": "TCS",
                "name": "Tata Consultancy",
                "sector": "Technology",
                "industry": "IT Services",
                "current_price": 3800.0,
                "market_cap_cr": 1380000,
                "fcf_cr": 40000,
                "debt_cr": 0,
                "cash_cr": 50000,
                "ebitda_cr": 60000,
                "eps": 130.0,
                "book_value_per_share": 350.0,
                "shares_outstanding_cr": 362.0,
                "business_description": "TCS is a global IT services company.",
                "buffett_quant_score": 9.0,
                "lynch_quant_score": 5.5,
                "composite_screen_score": 8.1,
            },
        ],
    }

    MOCK_REPORT = {
        "ticker": "RELIANCE",
        "name": "Reliance Industries",
        "sector": "Energy",
        "final_rating": "Strong Research Candidate",
        "category": "long_term_compounder",
        "current_price": 2850.0,
        "market_cap_cr": 1930000,
        "financial_strength_score": 8.0,
        "growth_score": 7.0,
        "valuation_score": 6.0,
        "moat_score": 8.0,
        "fisher_score": 7.5,
        "unicorn_score": 5.0,
        "sentiment_score": 6.0,
        "risk_score": 2.0,
        "pe_ratio": 30.0,
        "pb_ratio": 3.4,
        "peg_ratio": 1.2,
        "dividend_yield": 0.0035,
        "dcf_intrinsic_value": 3200.0,
        "roe": 0.18,
        "debt_equity": 0.4,
        "revenue_cagr_3y": 0.15,
        "profit_cagr_3y": 0.12,
        "fcf_cr": 45000,
        "promoter_holding_pct": 50.3,
        "promoter_pledge_pct": 0.0,
        "red_flags": [],
        "news_sentiment": "Positive",
        "news_summary": "Strong results.",
        "moat_summary": "Strong brand.",
        "fisher_summary": "Visionary management.",
        "ten_x_potential": False,
        "growth_ceiling": "medium",
        "scuttlebutt_signals": [],
        "unicorn_summary": "Large cap.",
        "emerging_themes": ["digital infrastructure"],
        "unicorn_size": "large_cap",
        "ten_x_candidate": False,
        "watch_triggers": [],
        "market_sentiment": "Bullish",
        "hype_detected": False,
        "accumulation_signal": True,
        "retail_buzz_level": "Medium",
        "business_summary": "Reliance is India's largest company.",
        "bull_case": ["Jio growth", "FCF positive"],
        "bear_case": ["Capex heavy"],
        "ideal_investor_type": "Long-term value investor",
        "confidence_pct": 75.0,
        "disclaimer": "Educational only.",
    }

    def test_run_produces_all_category_keys(self):
        cfg = make_cfg()
        scanner = UniverseScanOrchestrator(config=cfg)

        with patch.object(scanner.screener, "screen", return_value=self.MOCK_SCREEN_RESULT):
            with patch.object(scanner.earnings_agent, "analyze",
                              return_value={"earnings_quality_score": 7.0, "trends": {}, "quarters": []}):
                with patch.object(scanner.orchestrator, "research",
                                  return_value=dict(self.MOCK_REPORT)):
                    result = scanner.run(stage1_top_n=5, stage2_top_n=2)

        expected_keys = [
            "generated_at", "completed_at", "duration_seconds", "scan_stats",
            "top10_buffett", "top10_lynch", "top10_fisher", "top10_growth",
            "top10_small_cap", "top10_emerging_themes", "top10_dividend", "top10_avoid",
            "all_reports_summary", "disclaimer",
        ]
        for key in expected_keys:
            assert key in result, f"Missing key: {key}"

    def test_run_stats_populated(self):
        cfg = make_cfg()
        scanner = UniverseScanOrchestrator(config=cfg)

        with patch.object(scanner.screener, "screen", return_value=self.MOCK_SCREEN_RESULT):
            with patch.object(scanner.earnings_agent, "analyze",
                              return_value={"earnings_quality_score": 7.0, "trends": {}, "quarters": []}):
                with patch.object(scanner.orchestrator, "research",
                                  return_value=dict(self.MOCK_REPORT)):
                    result = scanner.run(stage1_top_n=5, stage2_top_n=2)

        stats = result["scan_stats"]
        assert stats["symbols_scanned"] == 100
        assert stats["deep_analysed"] == 2

    def test_run_handles_orchestrator_failure(self):
        cfg = make_cfg()
        scanner = UniverseScanOrchestrator(config=cfg)

        with patch.object(scanner.screener, "screen", return_value=self.MOCK_SCREEN_RESULT):
            with patch.object(scanner.earnings_agent, "analyze",
                              return_value={"earnings_quality_score": 5.0, "trends": {}, "quarters": []}):
                with patch.object(scanner.orchestrator, "research",
                                  side_effect=Exception("LLM timeout")):
                    result = scanner.run(stage1_top_n=5, stage2_top_n=2)

        assert result["scan_stats"]["errors"] == 2
        error_reports = [r for r in result["all_reports_summary"] if r["final_rating"] == "error"]
        assert len(error_reports) == 2

    def test_run_progress_callback_called(self):
        cfg = make_cfg()
        scanner = UniverseScanOrchestrator(config=cfg)
        calls = []

        def cb(stage, done, total, msg):
            calls.append(stage)

        with patch.object(scanner.screener, "screen", return_value=self.MOCK_SCREEN_RESULT):
            with patch.object(scanner.earnings_agent, "analyze",
                              return_value={"earnings_quality_score": 5.0, "trends": {}, "quarters": []}):
                with patch.object(scanner.orchestrator, "research",
                                  return_value=dict(self.MOCK_REPORT)):
                    scanner.run(stage1_top_n=5, stage2_top_n=1, progress_callback=cb)

        assert "stage1" in calls or "stage2" in calls or "ranking" in calls

    def test_run_enriches_report_with_earnings_data(self):
        cfg = make_cfg()
        scanner = UniverseScanOrchestrator(config=cfg)
        screen_result = dict(self.MOCK_SCREEN_RESULT)
        screen_result["candidates"] = [screen_result["candidates"][0]]

        eq_data = {
            "earnings_quality_score": 8.5,
            "trends": {"revenue_yoy_growth": 0.22, "profit_yoy_growth": 0.25,
                       "margin_expanding": True, "earnings_accelerating": True},
            "quarters": [],
        }
        report_without_cagr = dict(self.MOCK_REPORT, revenue_cagr_3y=None, profit_cagr_3y=None)

        with patch.object(scanner.screener, "screen", return_value=screen_result):
            with patch.object(scanner.earnings_agent, "analyze", return_value=eq_data):
                with patch.object(scanner.orchestrator, "research", return_value=report_without_cagr):
                    result = scanner.run(stage1_top_n=2, stage2_top_n=1)

        # earnings_quality_score should be set in summary
        summary = result["all_reports_summary"]
        assert any(r.get("earnings_quality_score") == 8.5 for r in summary)

    def test_lynch_scoring(self):
        report = {
            "peg_ratio": 0.7,
            "revenue_cagr_3y": 0.25,
            "profit_cagr_3y": 0.30,
            "earnings_quality_score": 8.0,
            "risk_score": 2.0,
        }
        score = _score_lynch(report)
        assert score > 5

    def test_lynch_high_peg_scores_lower(self):
        low_peg = {"peg_ratio": 0.5, "revenue_cagr_3y": 0.20, "profit_cagr_3y": 0.25,
                   "earnings_quality_score": 7.0, "risk_score": 2.0}
        high_peg = {"peg_ratio": 3.0, "revenue_cagr_3y": 0.20, "profit_cagr_3y": 0.25,
                    "earnings_quality_score": 7.0, "risk_score": 2.0}
        assert _score_lynch(low_peg) > _score_lynch(high_peg)

    def test_pick_top10_returns_max_10(self):
        reports = [
            {
                "ticker": f"S{i}", "final_rating": "Strong Research Candidate",
                "roe": 0.15, "moat_score": 7.0, "risk_score": 2.0,
                "financial_strength_score": 7.0, "category": "long_term_compounder",
                "current_price": 1000, "market_cap_cr": 50000,
                "revenue_cagr_3y": 0.15, "profit_cagr_3y": 0.12,
                "fisher_score": 7.0, "unicorn_score": 5.0, "sentiment_score": 6.0,
                "dividend_yield": 0.02, "peg_ratio": 1.2, "pe_ratio": 20, "pb_ratio": 3,
                "emerging_themes": [], "ten_x_potential": False, "ten_x_candidate": False,
                "earnings_quality_score": 7.0, "growth_ceiling": "medium",
                "red_flags": [], "bull_case": [], "bear_case": [], "moat_summary": "",
                "business_summary": "", "watch_triggers": [], "name": f"Stock{i}", "sector": "Tech",
            }
            for i in range(15)
        ]
        from src.agents.daily_report import _score_buffett
        top = _pick_top10(reports, _score_buffett)
        assert len(top) <= 10

    def test_pick_top10_structure(self):
        report = {
            "ticker": "TEST", "name": "Test Corp", "sector": "Tech",
            "final_rating": "Strong Research Candidate", "category": "growth",
            "current_price": 1000, "market_cap_cr": 5000,
            "roe": 0.20, "moat_score": 8.0, "risk_score": 1.0, "financial_strength_score": 8.0,
            "revenue_cagr_3y": 0.25, "profit_cagr_3y": 0.30, "growth_score": 9.0,
            "peg_ratio": 0.8, "pe_ratio": 25, "pb_ratio": 4, "fisher_score": 8.0,
            "unicorn_score": 7.0, "sentiment_score": 7.0, "dividend_yield": 0.01,
            "emerging_themes": ["AI"], "ten_x_potential": True, "ten_x_candidate": True,
            "earnings_quality_score": 8.5, "growth_ceiling": "high",
            "red_flags": [], "bull_case": ["Strong growth"], "bear_case": ["Valuation"],
            "moat_summary": "Strong moat", "business_summary": "Great company",
            "watch_triggers": ["Revenue > ₹1000 Cr"], "dcf_intrinsic_value": 1200.0,
        }
        from src.agents.daily_report import _score_buffett
        picks = _pick_top10([report], _score_buffett)
        assert len(picks) == 1
        p = picks[0]
        assert "ticker" in p and "score" in p and "key_metrics" in p
        assert "synopsis" in p and "bull_case" in p
        assert p["key_metrics"]["earnings_quality_score"] == 8.5


# -----------------------------------------------------------------------
# JobStore tests
# -----------------------------------------------------------------------

class TestJobStore:

    def setup_method(self):
        """Clear job store before each test."""
        import src.api.job_store as js
        with js._lock:
            js._jobs.clear()

    def test_create_and_get_job(self):
        job_id = job_store.create_job("universe_scan", {"stage1_top_n": 100})
        job = job_store.get_job(job_id)

        assert job is not None
        assert job["job_id"] == job_id
        assert job["status"] == "pending"
        assert job["job_type"] == "universe_scan"

    def test_start_job(self):
        job_id = job_store.create_job()
        job_store.start_job(job_id)
        job = job_store.get_job(job_id)
        assert job["status"] == "running"
        assert job["started_at"] is not None

    def test_complete_job(self):
        job_id = job_store.create_job()
        job_store.start_job(job_id)
        job_store.complete_job(job_id, {"result": "data"})
        job = job_store.get_job(job_id)
        assert job["status"] == "complete"
        assert job["result"] == {"result": "data"}
        assert job["progress"]["pct"] == 100

    def test_fail_job(self):
        job_id = job_store.create_job()
        job_store.start_job(job_id)
        job_store.fail_job(job_id, "Something went wrong")
        job = job_store.get_job(job_id)
        assert job["status"] == "failed"
        assert "Something went wrong" in job["error"]

    def test_update_progress(self):
        job_id = job_store.create_job()
        job_store.start_job(job_id)
        job_store.update_progress(job_id, "stage1", 50, 100, "Halfway done")
        job = job_store.get_job(job_id)
        assert job["progress"]["pct"] == 50
        assert job["progress"]["message"] == "Halfway done"
        assert job["progress"]["stage"] == "stage1"

    def test_get_nonexistent_job(self):
        result = job_store.get_job("nonexistent-id")
        assert result is None

    def test_list_jobs_returns_recent(self):
        job_id1 = job_store.create_job()
        job_id2 = job_store.create_job()
        jobs = job_store.list_jobs(limit=5)
        ids = [j["job_id"] for j in jobs]
        assert job_id1 in ids
        assert job_id2 in ids

    def test_list_jobs_no_result_payload(self):
        job_id = job_store.create_job()
        job_store.complete_job(job_id, {"big": "result" * 1000})
        jobs = job_store.list_jobs()
        for j in jobs:
            assert "result" not in j  # result should not be in list view

    def test_thread_safety(self):
        """Multiple threads creating/updating jobs should not cause races."""
        errors = []

        def worker():
            try:
                jid = job_store.create_job()
                job_store.start_job(jid)
                job_store.update_progress(jid, "stage1", 1, 10)
                job_store.complete_job(jid, {"ok": True})
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == []

    def test_job_returns_copy_not_reference(self):
        """Mutations to the returned dict must not affect the store."""
        job_id = job_store.create_job()
        job = job_store.get_job(job_id)
        job["status"] = "hacked"
        original = job_store.get_job(job_id)
        assert original["status"] == "pending"
