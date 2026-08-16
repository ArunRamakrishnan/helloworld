"""Unicorn Detector Agent — finds small-cap, founder-led, emerging-sector opportunities."""
import json
from typing import Any, Dict, List, Optional

import anthropic

from src.agents.registry import AgentRegistry
from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.prompts import load_prompt
from src.utils.scoring import weighted_average
from src.utils.validators import validate_score

logger = get_logger(__name__)

# Sectors with strong structural tailwinds in India (2024-2030)
TAILWIND_SECTORS = {
    "defense", "aerospace", "semiconductor", "ev", "electric vehicle",
    "renewable", "solar", "wind", "data center", "cloud", "ai", "artificial intelligence",
    "specialty chemical", "api", "pharma", "diagnostic", "health tech",
    "fintech", "digital payment", "infrastructure", "logistics", "cold chain",
    "agri tech", "food processing", "textile", "electronics manufacturing",
}


@AgentRegistry.register("unicorn")
class UnicornDetectorAgent:
    """
    Identifies small-cap, founder-led, emerging-sector stocks with 10x potential.
    Scoring combines quantitative filters + LLM qualitative assessment.
    Weights/thresholds come from config.scoring.unicorn; the system prompt lives in
    prompts/system/unicorn.md.
    """

    DIMENSIONS = [
        "market_size_opportunity",
        "founder_quality",
        "tech_adoption",
        "sector_tailwind",
        "competitive_position",
        "scalability",
        "disruption_potential",
    ]

    output_key = "unicorn"

    @staticmethod
    def pipeline_kwargs(ticker: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "business_description": context.get("business_description", ""),
            "market_cap_cr": context.get("market_cap_cr"),
            "revenue_cagr": context.get("revenue_cagr_3y"),
            "profit_cagr": context.get("profit_cagr_3y"),
            "roe": context.get("roe"),
            "debt_equity": context.get("debt_equity"),
            "promoter_holding_pct": context.get("promoter_holding_pct"),
        }

    def __init__(self, config=None):
        self.cfg = config or get_config()
        # Scoring weights/thresholds always come from the real loaded config,
        # independent of whatever `config` object the caller injects (see
        # fundamental_agent.py).
        self.rules = get_config().scoring.unicorn
        self._client: Optional[anthropic.Anthropic] = None
        if self.cfg.llm.anthropic_api_key:
            self._client = anthropic.Anthropic(api_key=self.cfg.llm.anthropic_api_key)

    def _quant_filters(
        self,
        market_cap_cr: float,
        revenue_cagr: Optional[float],
        profit_cagr: Optional[float],
        roe: Optional[float],
        debt_equity: Optional[float],
        promoter_holding_pct: Optional[float],
    ) -> Dict[str, Any]:
        """Run quantitative unicorn filters."""
        size_label = (
            "small_cap" if market_cap_cr <= self.rules.small_cap_max_cr
            else "mid_cap" if market_cap_cr <= self.rules.mid_cap_max_cr
            else "large_cap"
        )

        flags = []
        score_boost = 0.0

        if market_cap_cr <= self.rules.small_cap_max_cr:
            flags.append("Small cap — high growth potential")
            score_boost += 1.0

        if revenue_cagr and revenue_cagr >= 0.25:
            flags.append(f"Strong revenue CAGR: {revenue_cagr*100:.1f}%")
            score_boost += 1.5
        elif revenue_cagr and revenue_cagr >= 0.15:
            flags.append(f"Good revenue CAGR: {revenue_cagr*100:.1f}%")
            score_boost += 0.5

        if profit_cagr and profit_cagr >= 0.25:
            flags.append(f"Strong profit CAGR: {profit_cagr*100:.1f}%")
            score_boost += 1.5

        if roe and roe >= 0.20:
            flags.append(f"High ROE: {roe*100:.1f}%")
            score_boost += 1.0

        if promoter_holding_pct and promoter_holding_pct >= 50:
            flags.append(f"High promoter holding: {promoter_holding_pct:.1f}% — founder alignment")
            score_boost += 1.0

        if debt_equity is not None and debt_equity <= 0.3:
            flags.append("Debt-free or near debt-free")
            score_boost += 0.5

        return {
            "size_label": size_label,
            "quant_flags": flags,
            "quant_score_boost": round(min(score_boost, self.rules.quant_score_boost_cap), 2),
        }

    def _sector_tailwind_score(self, business_description: str) -> float:
        desc_lower = business_description.lower()
        matches = sum(1 for sector in TAILWIND_SECTORS if sector in desc_lower)
        if matches >= 3:
            return 9.0
        if matches == 2:
            return 7.5
        if matches == 1:
            return 6.0
        return 4.0

    def _llm_score(self, ticker: str, business_description: str, quant: Dict) -> Dict[str, Any]:
        if not self._client:
            logger.warning("ANTHROPIC_API_KEY not set — using fallback unicorn score for %s", ticker)
            return self._fallback_score(ticker, quant)

        user_msg = (
            f"Company: {ticker}\n\n"
            f"Business Description:\n{business_description}\n\n"
            f"Quantitative Signals:\n{json.dumps(quant, indent=2)}\n\n"
            "Evaluate this company's unicorn potential. Respond as JSON."
        )
        try:
            message = self._client.messages.create(
                model=self.cfg.llm.model,
                max_tokens=self.cfg.llm.max_tokens_for("unicorn"),
                system=load_prompt("unicorn"),
                messages=[{"role": "user", "content": user_msg}],
            )
            data = json.loads(message.content[0].text.strip())
            logger.info("Unicorn LLM analysis complete for %s | score=%s", ticker, data.get("unicorn_score"))
            return data
        except Exception as exc:
            logger.error("Unicorn LLM failed for %s: %s", ticker, exc)
            return self._fallback_score(ticker, quant)

    def _fallback_score(self, ticker: str, quant: Dict) -> Dict[str, Any]:
        base = 5.0 + quant.get("quant_score_boost", 0)
        return {
            **{dim: min(base, 10.0) for dim in self.DIMENSIONS},
            "unicorn_summary": "Unicorn analysis unavailable — LLM not configured.",
            "emerging_themes": [],
            "unicorn_score": round(min(base, 10.0), 2),
            "risk_of_being_early": "Medium",
            "watch_triggers": [],
        }

    def overall_unicorn_score(self, scores: Dict[str, float], quant_boost: float) -> float:
        base = weighted_average([(scores.get(dim, 5.0), w) for dim, w in self.rules.weights.items()])
        return round(validate_score(min(10.0, base + quant_boost * 0.5), "unicorn_score"), 2)

    def analyze(
        self,
        ticker: str,
        business_description: str,
        market_cap_cr: float,
        revenue_cagr: Optional[float] = None,
        profit_cagr: Optional[float] = None,
        roe: Optional[float] = None,
        debt_equity: Optional[float] = None,
        promoter_holding_pct: Optional[float] = None,
    ) -> Dict[str, Any]:
        logger.info("Unicorn detection for %s (mcap=%.0f cr)", ticker, market_cap_cr)

        quant = self._quant_filters(
            market_cap_cr, revenue_cagr, profit_cagr, roe, debt_equity, promoter_holding_pct
        )
        llm_data = self._llm_score(ticker, business_description, quant)

        # Use LLM unicorn_score if available, else compute from dimensions
        if "unicorn_score" in llm_data and isinstance(llm_data["unicorn_score"], (int, float)):
            final_score = round(validate_score(
                llm_data["unicorn_score"] + quant["quant_score_boost"] * 0.3,
                "unicorn_score"
            ), 2)
        else:
            final_score = self.overall_unicorn_score(llm_data, quant["quant_score_boost"])

        return {
            "ticker": ticker,
            "unicorn_score": final_score,
            "size_label": quant["size_label"],
            "dimension_scores": {d: llm_data.get(d, 5.0) for d in self.DIMENSIONS},
            "unicorn_summary": llm_data.get("unicorn_summary", ""),
            "emerging_themes": llm_data.get("emerging_themes", []),
            "quant_flags": quant["quant_flags"],
            "risk_of_being_early": llm_data.get("risk_of_being_early", "Medium"),
            "watch_triggers": llm_data.get("watch_triggers", []),
            "ten_x_candidate": final_score >= self.rules.ten_x_candidate_threshold,
        }
