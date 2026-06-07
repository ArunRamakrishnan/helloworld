"""Unit tests for RiskAgent — red flag detection and risk scoring."""
import pytest
from src.agents.risk_agent import RiskAgent


class TestRiskAgent:
    def setup_method(self):
        self.agent = RiskAgent()

    # ------------------------------------------------------------------
    # Red flag detection — positive scenarios (flags should be raised)
    # ------------------------------------------------------------------

    def test_high_debt_flag_detected(self):
        flags = self.agent.detect_red_flags({"debt_equity": 2.5, "ticker": "TEST"})
        flag_keys = [f[0] for f in flags]
        assert "high_debt" in flag_keys

    def test_negative_fcf_flag_detected(self):
        flags = self.agent.detect_red_flags({"fcf_cr": -100, "ticker": "TEST"})
        assert "negative_fcf" in [f[0] for f in flags]

    def test_high_promoter_pledge_flag(self):
        flags = self.agent.detect_red_flags({"promoter_pledge_pct": 45, "ticker": "TEST"})
        assert "high_promoter_pledge" in [f[0] for f in flags]

    def test_low_promoter_holding_flag(self):
        flags = self.agent.detect_red_flags({"promoter_holding_pct": 20, "ticker": "TEST"})
        assert "low_promoter_holding" in [f[0] for f in flags]

    def test_overvalued_pe_flag(self):
        flags = self.agent.detect_red_flags({"pe_ratio": 80, "ticker": "TEST"})
        assert "overvalued_pe" in [f[0] for f in flags]

    def test_auditor_change_flag(self):
        flags = self.agent.detect_red_flags({"auditor_changed": True, "ticker": "TEST"})
        assert "auditor_change" in [f[0] for f in flags]

    def test_governance_issue_flag(self):
        flags = self.agent.detect_red_flags({"governance_issue": True, "ticker": "TEST"})
        assert "governance_issue" in [f[0] for f in flags]

    def test_sudden_price_spike_flag(self):
        flags = self.agent.detect_red_flags({"sudden_price_spike": True, "ticker": "TEST"})
        assert "sudden_price_spike" in [f[0] for f in flags]

    def test_negative_operating_cash_flow_flag(self):
        flags = self.agent.detect_red_flags({"operating_cash_flow_cr": -50, "ticker": "TEST"})
        assert "negative_cash_flow_ops" in [f[0] for f in flags]

    # ------------------------------------------------------------------
    # Negative scenarios (clean company — no flags)
    # ------------------------------------------------------------------

    def test_clean_company_no_flags(self):
        flags = self.agent.detect_red_flags({
            "ticker": "GOODCO",
            "debt_equity": 0.3,
            "fcf_cr": 500,
            "operating_cash_flow_cr": 600,
            "promoter_pledge_pct": 0,
            "promoter_holding_pct": 65,
            "pe_ratio": 18,
            "auditor_changed": False,
            "governance_issue": False,
            "sudden_price_spike": False,
        })
        assert flags == []

    def test_de_exactly_at_threshold_no_flag(self):
        flags = self.agent.detect_red_flags({"debt_equity": 2.0, "ticker": "TEST"})
        assert "high_debt" not in [f[0] for f in flags]

    def test_pe_exactly_at_threshold_no_flag(self):
        flags = self.agent.detect_red_flags({"pe_ratio": 60, "ticker": "TEST"})
        assert "overvalued_pe" not in [f[0] for f in flags]

    # ------------------------------------------------------------------
    # Risk scoring
    # ------------------------------------------------------------------

    def test_risk_score_zero_for_no_flags(self):
        score = self.agent.compute_risk_score([], de=0.2)
        assert score == 0.0

    def test_risk_score_severe_flags_higher(self):
        severe_flags = [("high_debt", ""), ("governance_issue", ""), ("negative_fcf", "")]
        mild_flags = [("low_promoter_holding", ""), ("overvalued_pe", "")]
        severe_score = self.agent.compute_risk_score(severe_flags, de=None)
        mild_score = self.agent.compute_risk_score(mild_flags, de=None)
        assert severe_score > mild_score

    def test_risk_score_capped_at_10(self):
        many_flags = [(f"flag_{i}", "") for i in range(20)]
        score = self.agent.compute_risk_score(many_flags, de=5.0)
        assert score <= 10.0

    # ------------------------------------------------------------------
    # Full analyze
    # ------------------------------------------------------------------

    def test_analyze_returns_all_keys(self):
        result = self.agent.analyze("TEST", {
            "debt_equity": 1.0,
            "fcf_cr": 100,
            "promoter_pledge_pct": 0,
            "promoter_holding_pct": 55,
            "pe_ratio": 20,
        })
        assert "risk_score" in result
        assert "red_flags" in result
        assert "risk_label" in result

    def test_analyze_high_risk_labeled_correctly(self):
        result = self.agent.analyze("BADCO", {
            "debt_equity": 3.5,
            "fcf_cr": -200,
            "governance_issue": True,
            "promoter_pledge_pct": 60,
            "pe_ratio": 90,
        })
        assert result["risk_label"] == "High Risk"
        assert result["risk_score"] > 5

    def test_analyze_low_risk_labeled_correctly(self):
        result = self.agent.analyze("GOODCO", {
            "debt_equity": 0.1,
            "fcf_cr": 1000,
            "governance_issue": False,
            "promoter_pledge_pct": 0,
            "pe_ratio": 15,
        })
        assert result["risk_label"] == "Low Risk"
