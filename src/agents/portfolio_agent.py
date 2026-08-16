"""Portfolio Construction Agent — suggests allocation bands based on user risk profile."""
from typing import Any, Dict, List, Optional

from src.agents.registry import AgentRegistry
from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.validators import validate_score

logger = get_logger(__name__)


@AgentRegistry.register("portfolio")
class PortfolioAgent:
    """
    Suggests portfolio allocation bands.
    Never recommends a portfolio without knowing the user's risk profile.
    Never suggests overconcentration.
    Skips suggestions if emergency fund is below config.scoring.portfolio.emergency_fund_min_months.
    All caps/weights are sourced from config.scoring.portfolio (config/default.yaml).
    """

    def __init__(self, config=None):
        self.cfg = config or get_config()
        # Scoring rules and disclaimer text always come from the real loaded config,
        # independent of whatever `config` object the caller injects (see
        # fundamental_agent.py).
        self.rules = get_config().scoring.portfolio
        self.disclaimer = get_config().disclaimer

    def validate_user_profile(self, profile: Dict[str, Any]) -> List[str]:
        """Returns list of issues with the profile. Empty list means profile is complete."""
        issues = []
        if not profile.get("risk_appetite"):
            issues.append("risk_appetite is required (conservative / moderate / aggressive)")
        if not profile.get("investment_horizon_years"):
            issues.append("investment_horizon_years is required")
        min_months = self.rules.emergency_fund_min_months
        ef = profile.get("emergency_fund_months", 0)
        if ef < min_months:
            issues.append(
                f"Emergency fund is only {ef} months — we recommend {min_months}+ months before investing"
            )
        return issues

    def suggest_allocation(
        self,
        user_profile: Dict[str, Any],
        research_reports: List[Dict[str, Any]],
        total_investment_amount: float,
    ) -> Dict[str, Any]:
        """
        Given a list of research reports (with scores and categories),
        suggest allocation bands in percentage and amount.
        """
        issues = self.validate_user_profile(user_profile)
        if issues:
            return {
                "error": "Incomplete user profile",
                "issues": issues,
                "disclaimer": self.disclaimer,
            }

        risk = user_profile.get("risk_appetite", "moderate").lower()
        max_single = self.rules.max_single_stock_pct.get(risk, 8.0)
        max_sector = self.rules.max_sector_pct.get(risk, 20.0)
        horizon = user_profile.get("investment_horizon_years", 3)

        risk_cutoff = self.rules.eligible_risk_score_max.get(risk, self.rules.eligible_risk_score_max["default"])
        # Only consider Strong Research Candidates and Watch-grade stocks
        eligible = [
            r for r in research_reports
            if r.get("final_rating") in ("Strong Research Candidate", "Watch")
            and r.get("risk_score", 10) <= risk_cutoff
        ]

        if not eligible:
            return {
                "message": "No eligible stocks found matching your risk profile.",
                "disclaimer": self.disclaimer,
            }

        # Score = average of financial + moat + valuation, penalised by risk score
        cw = self.rules.composite_weights

        def composite(r):
            fin = r.get("financial_strength_score", 0)
            moat = r.get("moat_score", 0)
            val = r.get("valuation_score", 0)
            risk_pen = r.get("risk_score", 5)
            return (
                fin * cw["financial"] + moat * cw["moat"] + val * cw["valuation"]
                - risk_pen * cw["risk_penalty"]
            )

        eligible.sort(key=composite, reverse=True)

        allocations = []
        sector_allocation: Dict[str, float] = {}
        remaining_pct = 100.0

        for report in eligible:
            ticker = report.get("ticker", "")
            sector = report.get("sector", "Unknown")
            rating = report.get("final_rating", "Watch")
            weight = max_single if rating == "Strong Research Candidate" else max_single * self.rules.non_strong_weight_factor

            sector_used = sector_allocation.get(sector, 0)
            if sector_used + weight > max_sector:
                weight = max(0, max_sector - sector_used)

            if weight <= 0 or remaining_pct <= 0:
                break

            weight = min(weight, remaining_pct)
            sector_allocation[sector] = sector_used + weight
            remaining_pct -= weight

            allocations.append({
                "ticker": ticker,
                "sector": sector,
                "final_rating": rating,
                "allocation_pct": round(weight, 2),
                "allocation_amount": round(total_investment_amount * weight / 100, 2),
            })

        logger.info(
            "Portfolio constructed | %d stocks | risk=%s | horizon=%dy",
            len(allocations), risk, horizon,
        )
        return {
            "risk_appetite": risk,
            "investment_horizon_years": horizon,
            "total_investment": total_investment_amount,
            "allocations": allocations,
            "cash_reserve_pct": round(remaining_pct, 2),
            "warning": (
                "These are allocation BANDS for research purposes only. "
                "Actual implementation requires a SEBI-registered adviser."
            ),
            "disclaimer": self.disclaimer,
        }
