"""Moat and Business Quality Agent — scores competitive advantages via LLM analysis."""
from typing import Any, Dict, List, Optional

import anthropic

from src.agents.registry import AgentRegistry
from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.prompts import load_prompt
from src.utils.scoring import weighted_average
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


@AgentRegistry.register("moat")
class MoatAgent:
    """
    Uses Claude LLM to evaluate moat dimensions.
    Falls back to a rule-based score if LLM is not available.
    Dimension weights come from config.scoring.moat; the system prompt lives in
    prompts/system/moat.md.
    """

    output_key = "moat"

    @staticmethod
    def pipeline_kwargs(ticker: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {"business_description": context.get("business_description", "")}

    def __init__(self, config=None):
        self.cfg = config or get_config()
        # Scoring rules always come from the real loaded config, independent of
        # whatever `config` object the caller injects (see fundamental_agent.py).
        self.rules = get_config().scoring.moat
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
                max_tokens=self.cfg.llm.max_tokens_for("moat"),
                system=load_prompt("moat"),
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
        """Returns a neutral score across all dimensions when LLM is unavailable."""
        fallback = self.rules.fallback_score
        return {dim: fallback for dim in MOAT_DIMENSIONS} | {"summary": "Moat analysis unavailable — LLM not configured."}

    def overall_moat_score(self, scores: Dict[str, float]) -> float:
        fallback = self.rules.fallback_score
        total = weighted_average([(scores.get(dim, fallback), w) for dim, w in self.rules.weights.items()])
        return round(validate_score(total, "moat_score"), 2)

    def analyze(self, ticker: str, business_description: str) -> Dict[str, Any]:
        logger.info("Moat analysis for %s", ticker)
        dimension_scores = self._llm_score(ticker, business_description)
        moat_score = self.overall_moat_score(dimension_scores)
        return {
            "ticker": ticker,
            "dimension_scores": {d: dimension_scores.get(d, self.rules.fallback_score) for d in MOAT_DIMENSIONS},
            "moat_summary": dimension_scores.get("summary", ""),
            "moat_score": moat_score,
        }
