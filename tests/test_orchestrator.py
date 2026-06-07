"""Unit tests for Orchestrator — mocked agent pipeline."""
import json
import pytest
from unittest.mock import MagicMock, patch

from src.agents.orchestrator import Orchestrator

SAMPLE_STATEMENTS = [
    {"period": "FY22", "period_type": "annual", "revenue_cr": 1000, "net_profit_cr": 100,
     "total_equity_cr": 500, "total_debt_cr": 200, "capex_cr": 50, "free_cash_flow_cr": 150},
    {"period": "FY23", "period_type": "annual", "revenue_cr": 1200, "net_profit_cr": 130,
     "total_equity_cr": 600, "total_debt_cr": 180, "capex_cr": 60, "free_cash_flow_cr": 200},
    {"period": "FY24", "period_type": "annual", "revenue_cr": 1500, "net_profit_cr": 170,
     "total_equity_cr": 700, "total_debt_cr": 150, "capex_cr": 70, "free_cash_flow_cr": 250},
]


def _make_orchestrator(with_llm=False):
    cfg = MagicMock()
    cfg.llm.anthropic_api_key = "fake-key" if with_llm else None
    cfg.llm.model = "claude-opus-4-8"
    cfg.news_api_key = None
    cfg.paper_trading = True
    return Orchestrator(config=cfg)


class TestOrchestrator:
    def test_research_returns_all_required_keys(self):
        orch = _make_orchestrator()
        result = orch.research(
            ticker="TCS",
            current_price=3500.0,
            market_cap_cr=1270000,
            statements=SAMPLE_STATEMENTS,
            business_description="TCS is a global IT services company.",
            eps=97.0,
            book_value_per_share=350.0,
            debt_cr=150,
            cash_cr=500,
            ebitda_cr=20000,
            fcf_cr=8000,
            shares_outstanding_cr=360,
        )
        required_keys = [
            "ticker", "current_price", "financial_strength_score",
            "valuation_score", "moat_score", "risk_score",
            "final_rating", "disclaimer",
        ]
        for key in required_keys:
            assert key in result, f"Missing key: {key}"

    def test_disclaimer_always_present(self):
        orch = _make_orchestrator()
        result = orch.research(
            ticker="INFY", current_price=1400, market_cap_cr=580000,
            statements=SAMPLE_STATEMENTS,
            business_description="Infosys provides IT services.",
        )
        assert "SEBI" in result["disclaimer"]

    def test_final_rating_is_valid_value(self):
        orch = _make_orchestrator()
        result = orch.research(
            ticker="WIPRO", current_price=450, market_cap_cr=230000,
            statements=SAMPLE_STATEMENTS,
            business_description="Wipro is an IT company.",
        )
        assert result["final_rating"] in ("Strong Research Candidate", "Watch", "Avoid")

    def test_scores_are_in_range(self):
        orch = _make_orchestrator()
        result = orch.research(
            ticker="HDFC", current_price=1800, market_cap_cr=340000,
            statements=SAMPLE_STATEMENTS,
            business_description="HDFC is a leading private sector bank.",
            eps=60, book_value_per_share=400, debt_cr=50000, cash_cr=20000,
            ebitda_cr=25000, fcf_cr=8000, shares_outstanding_cr=600,
        )
        for score_key in ["financial_strength_score", "valuation_score", "moat_score", "risk_score"]:
            score = result.get(score_key)
            if score is not None:
                assert 0 <= score <= 10, f"{score_key}={score} out of range"

    def test_invalid_ticker_raises(self):
        orch = _make_orchestrator()
        with pytest.raises(ValueError):
            orch.research(ticker="", current_price=100, market_cap_cr=1000,
                          statements=[], business_description="x")

    def test_growth_score_high_growth(self):
        orch = _make_orchestrator()
        fundamental = {"revenue_cagr_3y": 0.25, "profit_cagr_3y": 0.22}
        assert orch._growth_score(fundamental) == 10.0

    def test_growth_score_low_growth(self):
        orch = _make_orchestrator()
        fundamental = {"revenue_cagr_3y": 0.02, "profit_cagr_3y": 0.01}
        assert orch._growth_score(fundamental) == 2.0

    def test_rule_based_synthesis_strong_candidate(self):
        orch = _make_orchestrator()
        fundamental = {"financial_strength_score": 8.0, "red_flags": []}
        valuation = {"valuation_score": 7.0}
        moat = {"moat_score": 7.5}
        risk = {"risk_score": 2.0, "red_flags": []}
        result = orch._rule_based_synthesis(fundamental, valuation, moat, risk)
        assert result["final_rating"] == "Strong Research Candidate"

    def test_rule_based_synthesis_avoid_high_risk(self):
        orch = _make_orchestrator()
        fundamental = {"financial_strength_score": 3.0, "red_flags": []}
        valuation = {"valuation_score": 4.0}
        moat = {"moat_score": 3.0}
        risk = {"risk_score": 8.0, "red_flags": [{"description": "High debt"}]}
        result = orch._rule_based_synthesis(fundamental, valuation, moat, risk)
        assert result["final_rating"] == "Avoid"

    def test_llm_synthesis_with_mock(self):
        orch = _make_orchestrator(with_llm=True)
        llm_response = {
            "business_summary": "TCS is a global IT company.",
            "bull_case": ["High ROE", "Cash rich"],
            "bear_case": ["Rupee risk"],
            "ideal_investor_type": "Long-term investor",
            "final_rating": "Strong Research Candidate",
            "confidence_pct": 80,
            "category": "long_term_compounder",
        }
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text=json.dumps(llm_response))]
        orch._llm.messages.create = MagicMock(return_value=mock_msg)

        fundamental = {"financial_strength_score": 8.0, "roe": 0.25, "debt_equity": 0.2,
                       "revenue_cagr_3y": 0.18, "profit_cagr_3y": 0.20, "red_flags": []}
        valuation = {"valuation_score": 7.0, "pe_ratio": 22, "pb_ratio": 5, "peg_ratio": 1.2}
        moat = {"moat_score": 8.0, "moat_summary": "Strong brand"}
        risk = {"risk_score": 2.0, "red_flags": []}
        news = {"sentiment": "Positive", "key_facts": ["Strong Q4"]}

        result = orch._synthesize("TCS", fundamental, valuation, moat, risk, news)
        assert result["final_rating"] == "Strong Research Candidate"
        assert result["confidence_pct"] == 80

    def test_llm_synthesis_falls_back_on_error(self):
        orch = _make_orchestrator(with_llm=True)
        orch._llm.messages.create = MagicMock(side_effect=Exception("timeout"))
        fundamental = {"financial_strength_score": 8.0, "red_flags": []}
        valuation = {"valuation_score": 7.0}
        moat = {"moat_score": 7.0}
        risk = {"risk_score": 2.0, "red_flags": []}
        news = {"sentiment": "Positive", "key_facts": []}
        result = orch._synthesize("TCS", fundamental, valuation, moat, risk, news)
        assert "final_rating" in result  # graceful fallback
