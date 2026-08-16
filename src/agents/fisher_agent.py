"""Philip Fisher Agent — evaluates innovation, R&D, future potential, and management vision."""
import json
from typing import Any, Dict, Optional

import anthropic

from src.agents.registry import AgentRegistry
from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.prompts import load_prompt
from src.utils.scoring import weighted_average
from src.utils.validators import validate_score

logger = get_logger(__name__)


@AgentRegistry.register("fisher")
class PhilipFisherAgent:
    """
    Evaluates stocks through Philip Fisher's lens:
    R&D, innovation, management quality, future monopoly potential.
    Falls back to rule-based scoring if LLM is unavailable.
    Dimension weights come from config.scoring.fisher; the system prompt lives in
    prompts/system/fisher.md.
    """

    DIMENSIONS = [
        "rd_innovation",
        "sales_organisation",
        "profit_margins",
        "management_integrity",
        "management_vision",
        "employee_relations",
        "future_monopoly",
    ]

    output_key = "fisher"

    @staticmethod
    def pipeline_kwargs(ticker: str, context: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "business_description": context.get("business_description", ""),
            "revenue_cagr": context.get("revenue_cagr_3y"),
            "profit_cagr": context.get("profit_cagr_3y"),
            "roe": context.get("roe"),
        }

    def __init__(self, config=None):
        self.cfg = config or get_config()
        # Scoring weights always come from the real loaded config, independent of
        # whatever `config` object the caller injects (see fundamental_agent.py).
        self.rules = get_config().scoring.fisher
        self._client: Optional[anthropic.Anthropic] = None
        if self.cfg.llm.anthropic_api_key:
            self._client = anthropic.Anthropic(api_key=self.cfg.llm.anthropic_api_key)

    def _llm_score(self, ticker: str, business_description: str, financials: Dict[str, Any]) -> Dict[str, Any]:
        if not self._client:
            logger.warning("ANTHROPIC_API_KEY not set — using fallback Fisher score for %s", ticker)
            return self._fallback_score(ticker)

        user_msg = (
            f"Company: {ticker}\n\n"
            f"Business Description:\n{business_description}\n\n"
            f"Key Financial Indicators:\n{json.dumps(financials, indent=2)}\n\n"
            "Score all 7 Fisher dimensions as JSON. Be analytical and honest."
        )
        try:
            message = self._client.messages.create(
                model=self.cfg.llm.model,
                max_tokens=self.cfg.llm.max_tokens_for("fisher"),
                system=load_prompt("fisher"),
                messages=[{"role": "user", "content": user_msg}],
            )
            data = json.loads(message.content[0].text.strip())
            logger.info("Fisher LLM analysis complete for %s | 10x=%s", ticker, data.get("ten_x_potential"))
            return data
        except Exception as exc:
            logger.error("Fisher LLM analysis failed for %s: %s", ticker, exc)
            return self._fallback_score(ticker)

    def _fallback_score(self, ticker: str) -> Dict[str, Any]:
        fallback = self.rules.fallback_score
        return {
            **{dim: fallback for dim in self.DIMENSIONS},
            "fisher_summary": "Philip Fisher analysis unavailable — LLM not configured.",
            "scuttlebutt_signals": [],
            "growth_ceiling": "medium",
            "ten_x_potential": False,
        }

    def overall_fisher_score(self, scores: Dict[str, float]) -> float:
        fallback = self.rules.fallback_score
        total = weighted_average([(scores.get(dim, fallback), w) for dim, w in self.rules.weights.items()])
        return round(validate_score(total, "fisher_score"), 2)

    def analyze(
        self,
        ticker: str,
        business_description: str,
        revenue_cagr: Optional[float] = None,
        profit_cagr: Optional[float] = None,
        roe: Optional[float] = None,
    ) -> Dict[str, Any]:
        logger.info("Philip Fisher analysis for %s", ticker)
        financials = {
            "revenue_cagr_3y_pct": round((revenue_cagr or 0) * 100, 1),
            "profit_cagr_3y_pct": round((profit_cagr or 0) * 100, 1),
            "roe_pct": round((roe or 0) * 100, 1),
        }
        scores = self._llm_score(ticker, business_description, financials)
        fisher_score = self.overall_fisher_score(scores)

        return {
            "ticker": ticker,
            "fisher_score": fisher_score,
            "dimension_scores": {d: scores.get(d, 5.0) for d in self.DIMENSIONS},
            "fisher_summary": scores.get("fisher_summary", ""),
            "scuttlebutt_signals": scores.get("scuttlebutt_signals", []),
            "growth_ceiling": scores.get("growth_ceiling", "medium"),
            "ten_x_potential": scores.get("ten_x_potential", False),
        }
