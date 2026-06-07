"""Unit tests for PortfolioAgent — allocation suggestions and profile validation."""
import pytest
from src.agents.portfolio_agent import PortfolioAgent

SAMPLE_REPORTS = [
    {
        "ticker": "STOCKA",
        "sector": "IT",
        "final_rating": "Strong Research Candidate",
        "financial_strength_score": 8.5,
        "moat_score": 7.5,
        "valuation_score": 7.0,
        "risk_score": 2.0,
    },
    {
        "ticker": "STOCKB",
        "sector": "Banking",
        "final_rating": "Watch",
        "financial_strength_score": 6.0,
        "moat_score": 5.5,
        "valuation_score": 6.5,
        "risk_score": 3.5,
    },
    {
        "ticker": "STOCKC",
        "sector": "IT",
        "final_rating": "Strong Research Candidate",
        "financial_strength_score": 7.0,
        "moat_score": 6.5,
        "valuation_score": 7.5,
        "risk_score": 2.5,
    },
]

VALID_PROFILE = {
    "user_id": "test_user",
    "risk_appetite": "moderate",
    "investment_horizon_years": 5,
    "emergency_fund_months": 8,
}


class TestPortfolioAgent:
    def setup_method(self):
        self.agent = PortfolioAgent()

    # ------------------------------------------------------------------
    # Profile validation
    # ------------------------------------------------------------------

    def test_missing_risk_appetite_flagged(self):
        profile = {"investment_horizon_years": 5, "emergency_fund_months": 8}
        issues = self.agent.validate_user_profile(profile)
        assert any("risk_appetite" in i for i in issues)

    def test_missing_horizon_flagged(self):
        profile = {"risk_appetite": "moderate", "emergency_fund_months": 8}
        issues = self.agent.validate_user_profile(profile)
        assert any("investment_horizon_years" in i for i in issues)

    def test_insufficient_emergency_fund_flagged(self):
        profile = {**VALID_PROFILE, "emergency_fund_months": 3}
        issues = self.agent.validate_user_profile(profile)
        assert any("Emergency fund" in i for i in issues)

    def test_valid_profile_no_issues(self):
        issues = self.agent.validate_user_profile(VALID_PROFILE)
        assert issues == []

    def test_exactly_six_months_emergency_fund_accepted(self):
        profile = {**VALID_PROFILE, "emergency_fund_months": 6}
        issues = self.agent.validate_user_profile(profile)
        assert not any("Emergency fund" in i for i in issues)

    # ------------------------------------------------------------------
    # Allocation suggestion
    # ------------------------------------------------------------------

    def test_suggest_allocation_returns_allocations(self):
        result = self.agent.suggest_allocation(VALID_PROFILE, SAMPLE_REPORTS, 100000)
        assert "allocations" in result
        assert len(result["allocations"]) > 0

    def test_allocation_pct_not_exceed_single_stock_limit(self):
        result = self.agent.suggest_allocation(VALID_PROFILE, SAMPLE_REPORTS, 100000)
        for alloc in result["allocations"]:
            assert alloc["allocation_pct"] <= 8.0  # moderate max is 8%

    def test_allocation_total_not_exceed_100(self):
        result = self.agent.suggest_allocation(VALID_PROFILE, SAMPLE_REPORTS, 100000)
        total = sum(a["allocation_pct"] for a in result["allocations"])
        assert total <= 100.01  # floating point tolerance

    def test_same_sector_concentration_limited(self):
        # IT sector has 2 stocks — combined should not exceed sector limit
        result = self.agent.suggest_allocation(VALID_PROFILE, SAMPLE_REPORTS, 100000)
        it_total = sum(a["allocation_pct"] for a in result["allocations"] if a["sector"] == "IT")
        assert it_total <= 20.0  # moderate sector max

    def test_disclaimer_always_present(self):
        result = self.agent.suggest_allocation(VALID_PROFILE, SAMPLE_REPORTS, 100000)
        assert "disclaimer" in result
        assert "SEBI" in result["disclaimer"]

    def test_incomplete_profile_returns_error(self):
        bad_profile = {"user_id": "x", "emergency_fund_months": 2}
        result = self.agent.suggest_allocation(bad_profile, SAMPLE_REPORTS, 100000)
        assert "error" in result

    def test_no_eligible_stocks_returns_message(self):
        avoid_reports = [{**r, "risk_score": 9.0} for r in SAMPLE_REPORTS]
        result = self.agent.suggest_allocation(VALID_PROFILE, avoid_reports, 100000)
        assert "message" in result or "allocations" in result  # graceful empty result

    def test_conservative_profile_lower_single_stock_limit(self):
        conservative = {**VALID_PROFILE, "risk_appetite": "conservative"}
        result = self.agent.suggest_allocation(conservative, SAMPLE_REPORTS, 100000)
        for alloc in result.get("allocations", []):
            assert alloc["allocation_pct"] <= 5.0

    def test_allocation_amount_matches_pct(self):
        total = 200000
        result = self.agent.suggest_allocation(VALID_PROFILE, SAMPLE_REPORTS, total)
        for alloc in result.get("allocations", []):
            expected = total * alloc["allocation_pct"] / 100
            assert abs(alloc["allocation_amount"] - expected) < 0.01
