"""News and Sentiment Agent — summarises news and separates facts from opinion/hype."""
from typing import Any, Dict, List, Optional

import anthropic

from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

NEWS_SYSTEM_PROMPT = """You are a financial news analyst for Indian equities.
Given a list of news articles about a stock, you must:
1. Summarise verified facts (earnings, filings, management changes, regulatory actions).
2. Identify sentiment: Positive / Neutral / Negative.
3. Flag any hype or unverified social-media speculation and label it "unverified".
4. Warn if articles discuss pump-and-dump patterns or suspicious activity.

Respond as JSON with keys:
- summary: 3-5 sentence factual summary
- sentiment: "Positive" | "Neutral" | "Negative" | "Mixed"
- key_facts: list of strings (verified facts only)
- unverified_claims: list of strings (hype/speculation to ignore)
- warnings: list of strings (governance, regulatory, suspicious patterns)

This is educational research. Not financial advice."""


class NewsAgent:
    """Summarises news using Claude LLM. Falls back to keyword-based analysis."""

    def __init__(self, config=None):
        self.cfg = config or get_config()
        self._client: Optional[anthropic.Anthropic] = None
        if self.cfg.llm.anthropic_api_key:
            self._client = anthropic.Anthropic(api_key=self.cfg.llm.anthropic_api_key)

    def _format_articles(self, articles: List[Dict[str, Any]]) -> str:
        lines = []
        for i, a in enumerate(articles[:20], 1):  # cap at 20 articles
            lines.append(
                f"{i}. [{a.get('source', 'Unknown')}] {a.get('published_at', '')} "
                f"— {a.get('title', '')}: {a.get('description', '')}"
            )
        return "\n".join(lines)

    def _llm_analyze(self, ticker: str, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not self._client:
            return self._keyword_fallback(ticker, articles)

        articles_text = self._format_articles(articles)
        user_msg = f"Stock: {ticker}\n\nNews Articles:\n{articles_text}\n\nAnalyze and respond as JSON."
        try:
            msg = self._client.messages.create(
                model=self.cfg.llm.model,
                max_tokens=1024,
                system=NEWS_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            )
            import json
            return json.loads(msg.content[0].text.strip())
        except Exception as exc:
            logger.error("News LLM analysis failed for %s: %s", ticker, exc)
            return self._keyword_fallback(ticker, articles)

    def _keyword_fallback(self, ticker: str, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        positive_words = {"growth", "profit", "record", "upgrade", "buy", "strong", "beat"}
        negative_words = {"loss", "decline", "downgrade", "sell", "fraud", "penalty", "cut", "miss"}
        pos = neg = 0
        titles = [a.get("title", "").lower() for a in articles]
        for title in titles:
            pos += sum(1 for w in positive_words if w in title)
            neg += sum(1 for w in negative_words if w in title)
        sentiment = "Mixed" if pos > 0 and neg > 0 else ("Positive" if pos > neg else "Negative" if neg > pos else "Neutral")
        return {
            "summary": f"{len(articles)} articles found. Keyword sentiment: {sentiment}. LLM not configured.",
            "sentiment": sentiment,
            "key_facts": [],
            "unverified_claims": [],
            "warnings": [],
        }

    def analyze(self, ticker: str, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.info("News analysis for %s (%d articles)", ticker, len(articles))
        if not articles:
            return {
                "ticker": ticker,
                "summary": "No recent news found.",
                "sentiment": "Neutral",
                "key_facts": [],
                "unverified_claims": [],
                "warnings": [],
            }
        result = self._llm_analyze(ticker, articles)
        result["ticker"] = ticker
        return result
