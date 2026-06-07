"""Unit tests for ValuationAgent — ratio calculations and DCF."""
import pytest
from src.agents.valuation_agent import ValuationAgent


class TestValuationAgent:
    def setup_method(self):
        self.agent = ValuationAgent()

    # ------------------------------------------------------------------
    # Ratio calculations
    # ------------------------------------------------------------------

    def test_pe_ratio_normal(self):
        assert self.agent.pe_ratio(100, 5) == pytest.approx(20.0)

    def test_pe_ratio_negative_eps_returns_none(self):
        assert self.agent.pe_ratio(100, -5) is None

    def test_pe_ratio_zero_eps_returns_none(self):
        assert self.agent.pe_ratio(100, 0) is None

    def test_pb_ratio_normal(self):
        assert self.agent.pb_ratio(200, 100) == pytest.approx(2.0)

    def test_pb_ratio_zero_book_returns_none(self):
        assert self.agent.pb_ratio(200, 0) is None

    def test_ev_ebitda_normal(self):
        result = self.agent.ev_ebitda(market_cap_cr=5000, debt_cr=1000, cash_cr=500, ebitda_cr=600)
        assert result == pytest.approx((5000 + 1000 - 500) / 600)

    def test_ev_ebitda_zero_ebitda_returns_none(self):
        assert self.agent.ev_ebitda(5000, 1000, 500, 0) is None

    def test_peg_ratio_normal(self):
        result = self.agent.peg_ratio(pe=20, earnings_growth_pct=15)
        assert result == pytest.approx(20 / 15)

    def test_peg_ratio_zero_growth_returns_none(self):
        assert self.agent.peg_ratio(20, 0) is None

    def test_dividend_yield_normal(self):
        result = self.agent.dividend_yield(10, 200)
        assert result == pytest.approx(0.05)

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def test_score_pe_graham_value(self):
        assert self.agent.score_pe(12) == 8.0

    def test_score_pe_very_low(self):
        assert self.agent.score_pe(8) == 10.0

    def test_score_pe_very_high(self):
        assert self.agent.score_pe(80) == 0.0

    def test_score_pb_graham_attractive(self):
        assert self.agent.score_pb(1.2) == 8.0

    def test_score_pb_expensive(self):
        assert self.agent.score_pb(6.0) == 1.0

    def test_score_peg_lynch_undervalued(self):
        assert self.agent.score_peg(0.4) == 10.0

    def test_score_peg_overvalued(self):
        assert self.agent.score_peg(2.5) == 1.0

    def test_score_margin_of_safety_deep_value(self):
        assert self.agent.score_margin_of_safety(60, 100) == 10.0

    def test_score_margin_of_safety_above_intrinsic(self):
        assert self.agent.score_margin_of_safety(120, 100) == 1.0

    # ------------------------------------------------------------------
    # DCF
    # ------------------------------------------------------------------

    def test_dcf_positive_fcf(self):
        result = self.agent.dcf_intrinsic_value(fcf_cr=100, shares_outstanding_cr=10)
        assert result["intrinsic_value_per_share_with_mos"] is not None
        assert result["intrinsic_value_per_share_with_mos"] > 0
        assert result["margin_of_safety_applied_pct"] == 30.0

    def test_dcf_negative_fcf_returns_error(self):
        result = self.agent.dcf_intrinsic_value(fcf_cr=-50)
        assert result.get("error") is not None

    def test_dcf_assumptions_shown(self):
        result = self.agent.dcf_intrinsic_value(fcf_cr=100)
        assert "assumptions" in result
        assert "growth_yr1_5_pct" in result["assumptions"]

    def test_dcf_custom_margin_of_safety(self):
        result_30 = self.agent.dcf_intrinsic_value(fcf_cr=100, margin_of_safety=0.30)
        result_40 = self.agent.dcf_intrinsic_value(fcf_cr=100, margin_of_safety=0.40)
        assert result_40["intrinsic_value_per_share_with_mos"] < result_30["intrinsic_value_per_share_with_mos"]

    # ------------------------------------------------------------------
    # Full analysis
    # ------------------------------------------------------------------

    def test_analyze_returns_all_keys(self):
        result = self.agent.analyze(
            ticker="HDFC", current_price=1800, market_cap_cr=340000,
            eps=60, book_value_per_share=400, debt_cr=50000, cash_cr=20000,
            ebitda_cr=25000, fcf_cr=8000, shares_outstanding_cr=600,
            profit_cagr=0.15, dividend_per_share=19,
        )
        for key in ["pe_ratio", "pb_ratio", "ev_ebitda", "peg_ratio", "valuation_score", "dcf"]:
            assert key in result

    def test_overall_valuation_score_in_range(self):
        score = self.agent.overall_valuation_score(15, 1.2, 0.8, 800, 1000)
        assert 0 <= score <= 10
