"""Tests for Phase 2 agents: PhilipFisherAgent, SentimentAgent, UnicornDetectorAgent, DailyReportOrchestrator."""
import json
from unittest.mock import MagicMock, patch, PropertyMock
from dataclasses import dataclass, field
from typing import Optional

import pytest

from src.agents.fisher_agent import PhilipFisherAgent
from src.agents.sentiment_agent import SentimentAgent
from src.agents.unicorn_detector import UnicornDetectorAgent, TAILWIND_SECTORS
from src.agents.daily_report import (
    DailyReportOrchestrator,
    _score_buffett, _score_growth, _score_small_cap,
    _score_emerging_theme, _score_dividend, _score_fisher, _score_avoid,
    _pick_top,
)


# ------------------------------------------------------------------
# Shared fixtures
# ------------------------------------------------------------------

@dataclass
class FakeLLM:
    anthropic_api_key: str = "fake-key"
    model: str = "claude-opus-4-8"
    max_tokens: int = 8192
    max_tokens_per_agent: dict = field(default_factory=dict)

    def max_tokens_for(self, agent: str) -> int:
        return self.max_tokens_per_agent.get(agent, self.max_tokens)


@dataclass
class FakeApp:
    llm: FakeLLM = field(default_factory=FakeLLM)
    news_api_key: Optional[str] = None
    paper_trading: bool = True
    log_level: str = "INFO"


def make_cfg(with_llm=True):
    cfg = FakeApp()
    if not with_llm:
        cfg.llm.anthropic_api_key = None
    return cfg


FISHER_LLM_RESPONSE = {
    "rd_innovation": 8.0,
    "sales_organisation": 7.0,
    "profit_margins": 7.5,
    "management_integrity": 9.0,
    "management_vision": 8.5,
    "employee_relations": 7.0,
    "future_monopoly": 8.0,
    "fisher_summary": "Strong R&D and visionary management.",
    "scuttlebutt_signals": ["Consistent R&D investment", "Employee retention high"],
    "growth_ceiling": "high",
    "ten_x_potential": True,
}

SENTIMENT_LLM_RESPONSE = {
    "overall_sentiment": "Bullish",
    "hype_detected": False,
    "fear_detected": False,
    "accumulation_signal": True,
    "retail_buzz_level": "Medium",
    "analyst_bias": "Positive",
    "sentiment_score": 7.5,
    "key_signals": ["Strong earnings beat", "FII buying"],
    "contrarian_note": "Consensus may be underestimating margin compression risk.",
}

UNICORN_LLM_RESPONSE = {
    "market_size_opportunity": 9.0,
    "founder_quality": 8.0,
    "tech_adoption": 8.5,
    "sector_tailwind": 9.0,
    "competitive_position": 7.5,
    "scalability": 8.0,
    "disruption_potential": 7.0,
    "unicorn_summary": "Strong unicorn candidate in defense sector.",
    "emerging_themes": ["defense indigenisation", "AI infrastructure"],
    "unicorn_score": 8.5,
    "risk_of_being_early": "Low",
    "watch_triggers": ["Order book growth > 30%", "Export order wins"],
}


# ------------------------------------------------------------------
# PhilipFisherAgent tests
# ------------------------------------------------------------------

class TestPhilipFisherAgent:

    def _mock_message(self, data):
        msg = MagicMock()
        msg.content = [MagicMock(text=json.dumps(data))]
        return msg

    def test_analyze_with_llm(self):
        cfg = make_cfg(with_llm=True)
        agent = PhilipFisherAgent(config=cfg)
        agent._client = MagicMock()
        agent._client.messages.create.return_value = self._mock_message(FISHER_LLM_RESPONSE)

        result = agent.analyze(
            "DIXON",
            "Dixon Technologies manufactures electronics and is a key PLI beneficiary.",
            revenue_cagr=0.35,
            profit_cagr=0.40,
            roe=0.22,
        )

        assert result["ticker"] == "DIXON"
        assert 0 <= result["fisher_score"] <= 10
        assert result["ten_x_potential"] is True
        assert result["growth_ceiling"] == "high"
        assert len(result["scuttlebutt_signals"]) > 0
        assert result["fisher_summary"] == "Strong R&D and visionary management."

    def test_analyze_fallback_no_llm(self):
        cfg = make_cfg(with_llm=False)
        agent = PhilipFisherAgent(config=cfg)

        result = agent.analyze(
            "SMALLCO",
            "Small company with no LLM configured but still needs a long description.",
        )

        assert result["ticker"] == "SMALLCO"
        assert result["fisher_score"] == 5.0
        assert result["ten_x_potential"] is False
        assert "LLM not configured" in result["fisher_summary"]

    def test_llm_failure_falls_back(self):
        cfg = make_cfg(with_llm=True)
        agent = PhilipFisherAgent(config=cfg)
        agent._client = MagicMock()
        agent._client.messages.create.side_effect = Exception("API error")

        result = agent.analyze(
            "FAIL",
            "Company with LLM that throws an exception during analysis.",
        )

        assert result["ticker"] == "FAIL"
        assert result["fisher_score"] == 5.0

    def test_overall_fisher_score_weights(self):
        cfg = make_cfg(with_llm=False)
        agent = PhilipFisherAgent(config=cfg)
        all_tens = {d: 10.0 for d in PhilipFisherAgent.DIMENSIONS}
        assert agent.overall_fisher_score(all_tens) == 10.0

        all_zeros = {d: 0.0 for d in PhilipFisherAgent.DIMENSIONS}
        assert agent.overall_fisher_score(all_zeros) == 0.0

    def test_llm_json_parse_error_falls_back(self):
        cfg = make_cfg(with_llm=True)
        agent = PhilipFisherAgent(config=cfg)
        agent._client = MagicMock()
        bad_msg = MagicMock()
        bad_msg.content = [MagicMock(text="not valid json {{")]
        agent._client.messages.create.return_value = bad_msg

        result = agent.analyze("X", "A company with a description that is long enough for validation.")
        assert result["fisher_score"] == 5.0

    def test_analyze_no_optional_financials(self):
        cfg = make_cfg(with_llm=False)
        agent = PhilipFisherAgent(config=cfg)
        result = agent.analyze("BARE", "Company with only required description field, nothing else provided.")
        assert "fisher_score" in result


# ------------------------------------------------------------------
# SentimentAgent tests
# ------------------------------------------------------------------

class TestSentimentAgent:

    def _mock_message(self, data):
        msg = MagicMock()
        msg.content = [MagicMock(text=json.dumps(data))]
        return msg

    def test_analyze_with_llm_no_rss(self):
        cfg = make_cfg(with_llm=True)
        agent = SentimentAgent(config=cfg)
        agent._client = MagicMock()
        agent._client.messages.create.return_value = self._mock_message(SENTIMENT_LLM_RESPONSE)

        with patch.object(agent, "fetch_rss_headlines", return_value=[]):
            result = agent.analyze("RELIANCE")

        assert result["ticker"] == "RELIANCE"
        assert result["overall_sentiment"] == "Bullish"
        assert result["accumulation_signal"] is True
        assert result["sentiment_score"] == 7.5

    def test_analyze_fallback_no_llm(self):
        cfg = make_cfg(with_llm=False)
        agent = SentimentAgent(config=cfg)

        with patch.object(agent, "fetch_rss_headlines", return_value=[]):
            result = agent.analyze("TCS")

        assert result["ticker"] == "TCS"
        assert result["overall_sentiment"] == "Neutral"
        assert result["sentiment_score"] == 5.0

    def test_rule_based_bullish(self):
        cfg = make_cfg(with_llm=False)
        agent = SentimentAgent(config=cfg)
        articles = [
            {"title": "Company reports record profit", "description": "Growth beats expectations"},
            {"title": "Strong upgrade from analyst", "description": "Buy recommendation issued"},
        ]
        result = agent._rule_based_sentiment("X", articles)
        assert result["overall_sentiment"] == "Bullish"

    def test_rule_based_bearish(self):
        cfg = make_cfg(with_llm=False)
        agent = SentimentAgent(config=cfg)
        articles = [
            {"title": "Company reports loss and decline", "description": "Fraud investigation opened"},
            {"title": "Penalty imposed, sell recommendation", "description": "Revenue miss"},
        ]
        result = agent._rule_based_sentiment("X", articles)
        assert result["overall_sentiment"] == "Bearish"

    def test_rule_based_hype_detection(self):
        cfg = make_cfg(with_llm=False)
        agent = SentimentAgent(config=cfg)
        articles = [
            {"title": "10x multibagger sure shot tip guaranteed", "description": "Must buy now"},
            {"title": "10x returns guaranteed", "description": "Multibagger alert"},
            {"title": "Sure shot tip of the day", "description": "guaranteed returns"},
        ]
        result = agent._rule_based_sentiment("PUMP", articles)
        assert result["hype_detected"] is True

    def test_rss_fetch_network_error_handled(self):
        cfg = make_cfg(with_llm=False)
        agent = SentimentAgent(config=cfg)
        with patch.object(agent._http, "get", side_effect=Exception("network error")):
            headlines = agent.fetch_rss_headlines("INFY")
        assert headlines == []

    def test_rss_fetch_filters_by_ticker(self):
        cfg = make_cfg(with_llm=False)
        agent = SentimentAgent(config=cfg)
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b"""<?xml version="1.0"?>
        <rss><channel>
          <item><title>RELIANCE quarterly results strong</title><description>Beat estimates</description></item>
          <item><title>Unrelated stock news today</title><description>Nothing here</description></item>
        </channel></rss>"""
        with patch.object(agent._http, "get", return_value=mock_resp):
            headlines = agent.fetch_rss_headlines("RELIANCE")
        assert any("RELIANCE" in h["title"].upper() for h in headlines)

    def test_rss_non_200_skipped(self):
        cfg = make_cfg(with_llm=False)
        agent = SentimentAgent(config=cfg)
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        with patch.object(agent._http, "get", return_value=mock_resp):
            headlines = agent.fetch_rss_headlines("TCS")
        assert headlines == []

    def test_analyze_with_extra_articles(self):
        cfg = make_cfg(with_llm=False)
        agent = SentimentAgent(config=cfg)
        extra = [{"title": "Company growth record profit", "description": "Strong beat", "source": "newsapi"}]
        with patch.object(agent, "fetch_rss_headlines", return_value=[]):
            result = agent.analyze("TCS", extra_articles=extra)
        assert result["headline_count"] == 1

    def test_llm_failure_falls_back(self):
        cfg = make_cfg(with_llm=True)
        agent = SentimentAgent(config=cfg)
        agent._client = MagicMock()
        agent._client.messages.create.side_effect = RuntimeError("LLM down")
        with patch.object(agent, "fetch_rss_headlines", return_value=[]):
            result = agent.analyze("HDFC")
        assert "overall_sentiment" in result

    def test_close(self):
        cfg = make_cfg(with_llm=False)
        agent = SentimentAgent(config=cfg)
        agent.close()  # should not raise


# ------------------------------------------------------------------
# UnicornDetectorAgent tests
# ------------------------------------------------------------------

class TestUnicornDetectorAgent:

    def _mock_message(self, data):
        msg = MagicMock()
        msg.content = [MagicMock(text=json.dumps(data))]
        return msg

    def test_analyze_small_cap_with_llm(self):
        cfg = make_cfg(with_llm=True)
        agent = UnicornDetectorAgent(config=cfg)
        agent._client = MagicMock()
        agent._client.messages.create.return_value = self._mock_message(UNICORN_LLM_RESPONSE)

        result = agent.analyze(
            "SMALLDEF",
            "Small defense company making AI-powered drone systems for Indian army.",
            market_cap_cr=2500,
            revenue_cagr=0.45,
            profit_cagr=0.50,
            roe=0.25,
            debt_equity=0.1,
            promoter_holding_pct=65.0,
        )

        assert result["ticker"] == "SMALLDEF"
        assert result["size_label"] == "small_cap"
        assert result["unicorn_score"] > 5
        assert result["ten_x_candidate"] is True
        assert "defense indigenisation" in result["emerging_themes"]

    def test_analyze_large_cap_fallback(self):
        cfg = make_cfg(with_llm=False)
        agent = UnicornDetectorAgent(config=cfg)

        result = agent.analyze(
            "BIGCO",
            "Large conglomerate operating in oil and gas with significant debt.",
            market_cap_cr=500000,
        )

        assert result["size_label"] == "large_cap"
        assert result["ten_x_candidate"] is False

    def test_quant_filters_small_cap_high_growth(self):
        cfg = make_cfg(with_llm=False)
        agent = UnicornDetectorAgent(config=cfg)
        quant = agent._quant_filters(
            market_cap_cr=3000,
            revenue_cagr=0.30,
            profit_cagr=0.35,
            roe=0.25,
            debt_equity=0.1,
            promoter_holding_pct=65.0,
        )
        assert quant["size_label"] == "small_cap"
        assert quant["quant_score_boost"] >= 3.0
        assert any("Small cap" in f for f in quant["quant_flags"])
        assert any("revenue CAGR" in f for f in quant["quant_flags"])

    def test_quant_filters_large_cap_no_growth(self):
        cfg = make_cfg(with_llm=False)
        agent = UnicornDetectorAgent(config=cfg)
        quant = agent._quant_filters(
            market_cap_cr=200000,
            revenue_cagr=0.03,
            profit_cagr=0.02,
            roe=0.08,
            debt_equity=2.5,
            promoter_holding_pct=25.0,
        )
        assert quant["size_label"] == "large_cap"
        assert quant["quant_score_boost"] == 0.0

    def test_sector_tailwind_defense(self):
        cfg = make_cfg(with_llm=False)
        agent = UnicornDetectorAgent(config=cfg)
        score = agent._sector_tailwind_score("defense aerospace manufacturer for Indian army")
        assert score >= 6.0

    def test_sector_tailwind_no_match(self):
        cfg = make_cfg(with_llm=False)
        agent = UnicornDetectorAgent(config=cfg)
        score = agent._sector_tailwind_score("Traditional brick and mortar shoe store")
        assert score == 4.0

    def test_sector_tailwind_multiple_themes(self):
        cfg = make_cfg(with_llm=False)
        agent = UnicornDetectorAgent(config=cfg)
        score = agent._sector_tailwind_score("AI data center cloud renewable solar energy company")
        assert score >= 7.5

    def test_overall_unicorn_score_clamps(self):
        cfg = make_cfg(with_llm=False)
        agent = UnicornDetectorAgent(config=cfg)
        scores = {d: 10.0 for d in UnicornDetectorAgent.DIMENSIONS}
        result = agent.overall_unicorn_score(scores, quant_boost=3.0)
        assert result <= 10.0

    def test_llm_failure_falls_back(self):
        cfg = make_cfg(with_llm=True)
        agent = UnicornDetectorAgent(config=cfg)
        agent._client = MagicMock()
        agent._client.messages.create.side_effect = Exception("timeout")
        result = agent.analyze("X", "A small company in emerging sector technology.", market_cap_cr=1000)
        assert "unicorn_score" in result

    def test_mid_cap_label(self):
        cfg = make_cfg(with_llm=False)
        agent = UnicornDetectorAgent(config=cfg)
        result = agent.analyze("MIDCO", "Mid cap company in specialty chemicals.", market_cap_cr=10000)
        assert result["size_label"] == "mid_cap"

    def test_tailwind_sectors_not_empty(self):
        assert len(TAILWIND_SECTORS) > 10


# ------------------------------------------------------------------
# Scoring function tests
# ------------------------------------------------------------------

class TestScoringFunctions:

    def _report(self, **kwargs):
        base = {
            "ticker": "TEST",
            "roe": 0.20,
            "moat_score": 7.0,
            "risk_score": 2.0,
            "financial_strength_score": 8.0,
            "revenue_cagr_3y": 0.20,
            "profit_cagr_3y": 0.25,
            "growth_score": 9.0,
            "peg_ratio": 0.8,
            "unicorn_score": 8.0,
            "unicorn_size": "small_cap",
            "emerging_themes": ["defense", "AI"],
            "sentiment_score": 7.0,
            "dividend_yield": 0.04,
            "fisher_score": 8.0,
            "ten_x_potential": True,
            "growth_ceiling": "high",
            "red_flags": [],
            "final_rating": "Strong Research Candidate",
        }
        base.update(kwargs)
        return base

    def test_score_buffett_high_roe(self):
        r = self._report(roe=0.30, moat_score=9.0, risk_score=1.0, financial_strength_score=9.0)
        assert _score_buffett(r) > 10

    def test_score_buffett_high_risk_penalised(self):
        low = self._report(risk_score=1.0)
        high = self._report(risk_score=9.0)
        assert _score_buffett(low) > _score_buffett(high)

    def test_score_growth_high_cagr(self):
        r = self._report(revenue_cagr_3y=0.40, profit_cagr_3y=0.45, growth_score=10.0, peg_ratio=0.5)
        assert _score_growth(r) > 15

    def test_score_small_cap_preferred(self):
        small = self._report(unicorn_size="small_cap")
        large = self._report(unicorn_size="large_cap")
        assert _score_small_cap(small) > _score_small_cap(large)

    def test_score_emerging_theme_more_themes(self):
        many = self._report(emerging_themes=["AI", "defense", "EV"])
        few = self._report(emerging_themes=[])
        assert _score_emerging_theme(many) > _score_emerging_theme(few)

    def test_score_dividend(self):
        high_div = self._report(dividend_yield=0.06)
        low_div = self._report(dividend_yield=0.01)
        assert _score_dividend(high_div) > _score_dividend(low_div)

    def test_score_fisher_ten_x(self):
        with_10x = self._report(ten_x_potential=True, growth_ceiling="high")
        without = self._report(ten_x_potential=False, growth_ceiling="low")
        assert _score_fisher(with_10x) > _score_fisher(without)

    def test_score_avoid_more_flags(self):
        many_flags = self._report(
            risk_score=8.0,
            red_flags=[{"key": "high_debt"}, {"key": "governance_issue"}, {"key": "promoter_pledge"}]
        )
        clean = self._report(risk_score=1.0, red_flags=[])
        assert _score_avoid(many_flags) > _score_avoid(clean)

    def test_pick_top_returns_n(self):
        reports = [self._report(ticker=f"S{i}", roe=0.1 * i) for i in range(1, 6)]
        top = _pick_top(reports, _score_buffett, n=3)
        assert len(top) <= 3

    def test_pick_top_excludes_error_reports(self):
        reports = [
            self._report(ticker="GOOD"),
            {"ticker": "BAD", "final_rating": "error"},
        ]
        top = _pick_top(reports, _score_buffett, n=3)
        assert all(p["ticker"] != "BAD" for p in top)

    def test_pick_top_min_score_filter(self):
        reports = [self._report(ticker="LOW", roe=0.01, moat_score=1.0, risk_score=9.0, financial_strength_score=1.0)]
        top = _pick_top(reports, _score_buffett, n=3, min_score=9999.0)
        assert top == []


# ------------------------------------------------------------------
# DailyReportOrchestrator tests
# ------------------------------------------------------------------

class TestDailyReportOrchestrator:

    SAMPLE_STOCK = {
        "ticker": "RELIANCE",
        "current_price": 2850.0,
        "market_cap_cr": 1930000,
        "business_description": "Reliance Industries diversified conglomerate petrochemicals retail digital Jio.",
        "eps": 96.0,
        "book_value_per_share": 850.0,
        "debt_cr": 312000,
        "cash_cr": 180000,
        "ebitda_cr": 160000,
        "fcf_cr": 45000,
        "shares_outstanding_cr": 677.0,
        "dividend_per_share": 10.0,
        "statements": [],
    }

    MOCK_REPORT = {
        "ticker": "RELIANCE",
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
        "ev_ebitda": 12.0,
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
        "news_summary": "Strong earnings.",
        "moat_summary": "Strong brand and distribution.",
        "fisher_summary": "Visionary management.",
        "ten_x_potential": False,
        "growth_ceiling": "medium",
        "scuttlebutt_signals": [],
        "unicorn_summary": "Large cap — limited unicorn upside.",
        "emerging_themes": [],
        "unicorn_size": "large_cap",
        "ten_x_candidate": False,
        "watch_triggers": [],
        "market_sentiment": "Bullish",
        "hype_detected": False,
        "accumulation_signal": True,
        "retail_buzz_level": "Medium",
        "business_summary": "Reliance is India's largest conglomerate.",
        "bull_case": ["Strong FCF", "Jio growth"],
        "bear_case": ["High debt"],
        "ideal_investor_type": "Long-term value investor",
        "confidence_pct": 75.0,
        "disclaimer": "Educational research only.",
    }

    def test_run_single_stock(self):
        cfg = make_cfg(with_llm=False)
        orch = DailyReportOrchestrator(config=cfg)
        with patch.object(orch.orchestrator, "research", return_value=self.MOCK_REPORT):
            report = orch.run([self.SAMPLE_STOCK])

        assert report["stocks_analysed"] == 1
        assert "generated_at" in report
        assert "top_buffett_stocks" in report
        assert "stocks_to_avoid" in report
        assert "disclaimer" in report

    def test_run_failed_stock_included_as_error(self):
        cfg = make_cfg(with_llm=False)
        orch = DailyReportOrchestrator(config=cfg)
        with patch.object(orch.orchestrator, "research", side_effect=Exception("boom")):
            report = orch.run([self.SAMPLE_STOCK])

        assert report["stocks_analysed"] == 1

    def test_run_multiple_stocks(self):
        cfg = make_cfg(with_llm=False)
        orch = DailyReportOrchestrator(config=cfg)
        stocks = [dict(self.SAMPLE_STOCK, ticker=f"S{i}") for i in range(5)]
        reports = [dict(self.MOCK_REPORT, ticker=f"S{i}") for i in range(5)]
        with patch.object(orch.orchestrator, "research", side_effect=reports):
            report = orch.run(stocks)

        assert report["stocks_analysed"] == 5
        assert len(report["top_buffett_stocks"]) <= 3

    def test_report_structure(self):
        cfg = make_cfg(with_llm=False)
        orch = DailyReportOrchestrator(config=cfg)
        with patch.object(orch.orchestrator, "research", return_value=self.MOCK_REPORT):
            report = orch.run([self.SAMPLE_STOCK])

        required_keys = [
            "generated_at", "stocks_analysed",
            "top_buffett_stocks", "top_growth_stocks",
            "top_small_cap_opportunities", "top_emerging_theme_stocks",
            "top_dividend_stocks", "top_fisher_stocks",
            "stocks_to_avoid", "portfolio_rebalancing_note", "disclaimer",
        ]
        for key in required_keys:
            assert key in report, f"Missing key: {key}"

    def test_top_pick_structure(self):
        cfg = make_cfg(with_llm=False)
        orch = DailyReportOrchestrator(config=cfg)
        with patch.object(orch.orchestrator, "research", return_value=self.MOCK_REPORT):
            report = orch.run([self.SAMPLE_STOCK])

        picks = report["top_buffett_stocks"]
        if picks:
            pick = picks[0]
            assert "ticker" in pick
            assert "final_rating" in pick
            assert "score" in pick
            assert "key_metrics" in pick
            assert "bull_case" in pick

    def test_avoid_list_excludes_strong_candidates_with_low_risk(self):
        cfg = make_cfg(with_llm=False)
        orch = DailyReportOrchestrator(config=cfg)
        clean_report = dict(self.MOCK_REPORT, risk_score=0.0, red_flags=[])
        with patch.object(orch.orchestrator, "research", return_value=clean_report):
            report = orch.run([self.SAMPLE_STOCK])
        assert all(p["ticker"] != "RELIANCE" for p in report["stocks_to_avoid"])
