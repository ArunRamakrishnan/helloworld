"""Philip Fisher Agent — evaluates innovation, R&D, future potential, and management vision."""
import json
from typing import Any, Dict, Optional

import anthropic

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.validators import validate_score

logger = get_logger(__name__)

FISHER_SYSTEM_PROMPT = """You are a Philip Fisher-style investment analyst.
Fisher's philosophy: invest in companies with outstanding growth prospects, visionary management,
strong R&D, and the potential to dominate their market for decades.

Evaluate the following Fisher dimensions on a 0-10 scale:
- rd_innovation: R&D investment and new product pipeline quality
- sales_organisation: strength and effectiveness of the sales/distribution organisation
- profit_margins: industry-leading and improving profit margins
- management_integrity: does management communicate honestly? Are promises kept?
- management_vision: does leadership have a long-term vision and execution track record?
- employee_relations: does the company attract and retain top talent?
- future_monopoly: potential to become a dominant player or near-monopoly in its sector

Key Fisher questions to answer:
- Can this become a future monopoly in its niche?
- Is management visionary and do they communicate clearly?
- Are new products or services driving future growth?
- Does the company have a growing addressable market?

Respond ONLY as valid JSON with keys matching the dimension names above (each a float 0-10).
Add:
- "fisher_summary": 3-4 sentences on the company's Fisher profile
- "scuttlebutt_signals": list of 2-3 positive signals a Fisher analyst would look for
- "growth_ceiling": "high" | "medium" | "low" — how large can this company get?
- "ten_x_potential": true | false — does this have 10x return potential over 10 years?

This is educational research. Not financial advice."""


class PhilipFisherAgent:
    """
    Evaluates stocks through Philip Fisher's lens:
    R&D, innovation, management quality, future monopoly potential.
    Falls back to rule-based scoring if LLM is unavailable.
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

    WEIGHTS = {
        "rd_innovation": 0.20,
        "sales_organisation": 0.10,
        "profit_margins": 0.15,
        "management_integrity": 0.15,
        "management_vision": 0.20,
        "employee_relations": 0.05,
        "future_monopoly": 0.15,
    }

    def __init__(self, config=None):
        self.cfg = config or get_config()
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
                max_tokens=1024,
                system=FISHER_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            )
            data = json.loads(message.content[0].text.strip())
            logger.info("Fisher LLM analysis complete for %s | 10x=%s", ticker, data.get("ten_x_potential"))
            return data
        except Exception as exc:
            logger.error("Fisher LLM analysis failed for %s: %s", ticker, exc)
            return self._fallback_score(ticker)

    def _fallback_score(self, ticker: str) -> Dict[str, Any]:
        return {
            **{dim: 5.0 for dim in self.DIMENSIONS},
            "fisher_summary": "Philip Fisher analysis unavailable — LLM not configured.",
            "scuttlebutt_signals": [],
            "growth_ceiling": "medium",
            "ten_x_potential": False,
        }

    def overall_fisher_score(self, scores: Dict[str, float]) -> float:
        total = sum(scores.get(dim, 5.0) * w for dim, w in self.WEIGHTS.items())
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
