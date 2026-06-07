"""Unit tests for FundamentalAgent — 100% business use case coverage."""
import pytest
from src.agents.fundamental_agent import FundamentalAgent, _cagr


# ------------------------------------------------------------------
# CAGR helper
# ------------------------------------------------------------------

def test_cagr_basic():
    result = _cagr(100, 200, 3)
    assert abs(result - 0.2599) < 0.001


def test_cagr_zero_start_returns_none():
    assert _cagr(0, 200, 3) is None


def test_cagr_negative_years_returns_none():
    assert _cagr(100, 200, 0) is None


def test_cagr_none_inputs():
    assert _cagr(None, 200, 3) is None


# ------------------------------------------------------------------
# Ratio calculations
# ------------------------------------------------------------------

class TestFundamentalAgent:
    def setup_method(self):
        self.agent = FundamentalAgent()

    def test_compute_roe_normal(self):
        roe = self.agent.compute_roe(net_profit_cr=200, equity_cr=1000)
        assert roe == pytest.approx(0.20)

    def test_compute_roe_zero_equity(self):
        assert self.agent.compute_roe(200, 0) is None

    def test_compute_debt_equity_normal(self):
        de = self.agent.compute_debt_equity(debt_cr=500, equity_cr=1000)
        assert de == pytest.approx(0.5)

    def test_compute_debt_equity_zero_equity(self):
        assert self.agent.compute_debt_equity(500, 0) is None

    def test_compute_interest_coverage_normal(self):
        ic = self.agent.compute_interest_coverage(ebit_cr=300, interest_cr=100)
        assert ic == pytest.approx(3.0)

    def test_compute_interest_coverage_zero_interest(self):
        assert self.agent.compute_interest_coverage(300, 0) is None

    def test_compute_fcf(self):
        fcf = self.agent.compute_fcf(operating_cash_flow_cr=500, capex_cr=150)
        assert fcf == pytest.approx(350.0)

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def test_score_roe_excellent(self):
        assert self.agent.score_roe(0.35) == 10.0

    def test_score_roe_good(self):
        assert self.agent.score_roe(0.22) == 8.0

    def test_score_roe_minimum_buffett(self):
        assert self.agent.score_roe(0.16) == 6.0

    def test_score_roe_poor(self):
        assert self.agent.score_roe(0.05) == 2.0

    def test_score_roe_negative(self):
        assert self.agent.score_roe(-0.1) == 0.0

    def test_score_roe_none(self):
        assert self.agent.score_roe(None) == 0.0

    def test_score_debt_equity_no_debt(self):
        assert self.agent.score_debt_equity(0) == 10.0

    def test_score_debt_equity_graham_safe(self):
        assert self.agent.score_debt_equity(0.4) == 8.0

    def test_score_debt_equity_high_risk(self):
        assert self.agent.score_debt_equity(2.5) == 1.0

    def test_score_revenue_cagr_high_growth(self):
        assert self.agent.score_revenue_cagr(0.25) == 10.0

    def test_score_revenue_cagr_negative(self):
        assert self.agent.score_revenue_cagr(-0.05) == 0.0

    # ------------------------------------------------------------------
    # Full analysis
    # ------------------------------------------------------------------

    def test_analyze_with_statements(self):
        statements = [
            {"period": "FY22", "period_type": "annual", "revenue_cr": 1000, "net_profit_cr": 100,
             "total_equity_cr": 500, "total_debt_cr": 200, "capex_cr": 50, "free_cash_flow_cr": 150},
            {"period": "FY23", "period_type": "annual", "revenue_cr": 1200, "net_profit_cr": 130,
             "total_equity_cr": 600, "total_debt_cr": 180, "capex_cr": 60, "free_cash_flow_cr": 200},
            {"period": "FY24", "period_type": "annual", "revenue_cr": 1500, "net_profit_cr": 170,
             "total_equity_cr": 700, "total_debt_cr": 150, "capex_cr": 70, "free_cash_flow_cr": 250},
        ]
        result = self.agent.analyze("TESTCO", statements)
        assert result["ticker"] == "TESTCO"
        assert "financial_strength_score" in result
        assert 0 <= result["financial_strength_score"] <= 10

    def test_analyze_empty_statements_returns_error(self):
        result = self.agent.analyze("TESTCO", [])
        assert "error" in result

    def test_analyze_with_quarterly_only_returns_none_cagr(self):
        statements = [
            {"period": "Q1FY24", "period_type": "quarterly", "revenue_cr": 300, "net_profit_cr": 30,
             "total_equity_cr": 500, "total_debt_cr": 100, "capex_cr": 20, "free_cash_flow_cr": 50},
        ]
        result = self.agent.analyze("TESTCO", statements)
        assert result.get("revenue_cagr_3y") is None
