"""Moat and Business Quality Agent — scores competitive advantages via LLM analysis."""
from typing import Any, Dict, List, Optional

import anthropic

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.validators import validate_score

logger = get_logger(__name__)

MOAT_DIMENSIONS = [
    "brand_power",
    "switching_cost",
    "network_effect",
    "cost_advantage",
    "regulatory_advantage",
    "distribution_strength",
    "management_quality",
]

MOAT_SYSTEM_PROMPT = """You are a senior investment analyst evaluating economic moats.
Score the following moat dimensions for the given company on a 0-10 scale:
- brand_power: strength of brand in pricing power and customer loyalty
- switching_cost: how hard it is for customers to leave
- network_effect: does the product get better as more people use it?
- cost_advantage: structural cost leadership vs peers
- regulatory_advantage: licenses, patents, government protection
- distribution_strength: reach and exclusivity of distribution channels
- management_quality: capital allocation track record, governance, integrity

Respond ONLY as valid JSON with keys matching the dimension names above, each mapped to a float 0-10.
Add a "summary" key with 2-3 sentences explaining the moat.
Do not include any other text outside the JSON.
This is educational research. Disclaimer: Not financial advice."""


class MoatAgent:
    """
    Uses Claude LLM to evaluate moat dimensions.
    Falls back to a rule-based score if LLM is not available.
    """

    def __init__(self, config=None):
        self.cfg = config or get_config()
        self._client: Optional[anthropic.Anthropic] = None
        if self.cfg.llm.anthropic_api_key:
            self._client = anthropic.Anthropic(api_key=self.cfg.llm.anthropic_api_key)

    def _llm_score(self, ticker: str, business_description: str) -> Dict[str, Any]:
        if not self._client:
            logger.warning("ANTHROPIC_API_KEY not set — using fallback moat score for %s", ticker)
            return self._fallback_score(ticker)

        user_msg = (
            f"Company: {ticker}\n\n"
            f"Business Description:\n{business_description}\n\n"
            "Score all 7 moat dimensions as JSON."
        )
        try:
            message = self._client.messages.create(
                model=self.cfg.llm.model,
                max_tokens=1024,
                system=MOAT_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            )
            import json
            raw = message.content[0].text.strip()
            data = json.loads(raw)
            logger.info("LLM moat analysis complete for %s", ticker)
            return data
        except Exception as exc:
            logger.error("LLM moat analysis failed for %s: %s", ticker, exc)
            return self._fallback_score(ticker)

    def _fallback_score(self, ticker: str) -> Dict[str, Any]:
        """Returns a neutral 5/10 across all dimensions when LLM is unavailable."""
        return {dim: 5.0 for dim in MOAT_DIMENSIONS} | {"summary": "Moat analysis unavailable — LLM not configured."}

    def overall_moat_score(self, scores: Dict[str, float]) -> float:
        weights = {
            "brand_power": 0.15,
            "switching_cost": 0.20,
            "network_effect": 0.15,
            "cost_advantage": 0.15,
            "regulatory_advantage": 0.10,
            "distribution_strength": 0.10,
            "management_quality": 0.15,
        }
        total = sum(scores.get(dim, 5.0) * w for dim, w in weights.items())
        return round(validate_score(total, "moat_score"), 2)

    def analyze(self, ticker: str, business_description: str) -> Dict[str, Any]:
        logger.info("Moat analysis for %s", ticker)
        dimension_scores = self._llm_score(ticker, business_description)
        moat_score = self.overall_moat_score(dimension_scores)
        return {
            "ticker": ticker,
            "dimension_scores": {d: dimension_scores.get(d, 5.0) for d in MOAT_DIMENSIONS},
            "moat_summary": dimension_scores.get("summary", ""),
            "moat_score": moat_score,
        }
