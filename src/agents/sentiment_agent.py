"""Sentiment Agent — aggregates signals from public RSS feeds and LLM analysis."""
import json
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree

import httpx
import anthropic

from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

SENTIMENT_SYSTEM_PROMPT = """You are a market sentiment analyst for Indian equities.
You will receive news headlines and summaries from financial portals.

Your job:
1. Detect overall market sentiment: Bullish | Bearish | Neutral | Mixed
2. Identify if there is excessive hype (pump risk) or panic (fear-driven selling)
3. Detect accumulation signals (consistent buying interest, institutional coverage)
4. Flag momentum signals (trending topics, analyst upgrades/downgrades)
5. Rate retail sentiment (social buzz level): Low | Medium | High

Respond ONLY as valid JSON with keys:
- overall_sentiment: "Bullish" | "Bearish" | "Neutral" | "Mixed"
- hype_detected: true | false
- fear_detected: true | false
- accumulation_signal: true | false
- retail_buzz_level: "Low" | "Medium" | "High"
- analyst_bias: "Positive" | "Negative" | "Neutral"
- sentiment_score: float 0-10 (10 = extremely bullish)
- key_signals: list of 2-4 most important signals found
- contrarian_note: one sentence on what the crowd may be missing

This is educational research. Not financial advice."""

# Public RSS feeds that don't require auth
RSS_SOURCES = {
    "moneycontrol": "https://www.moneycontrol.com/rss/results.xml",
    "economic_times": "https://economictimes.indiatimes.com/markets/stocks/rss.cms",
    "livemint": "https://www.livemint.com/rss/markets",
}


class SentimentAgent:
    """
    Aggregates sentiment from:
    1. Public RSS feeds (Moneycontrol, Economic Times, LiveMint)
    2. NewsAPI articles (if configured)
    3. LLM analysis of all signals

    Falls back to rule-based scoring if LLM unavailable.
    """

    def __init__(self, config=None):
        self.cfg = config or get_config()
        self._http = httpx.Client(timeout=10.0)
        self._client: Optional[anthropic.Anthropic] = None
        if self.cfg.llm.anthropic_api_key:
            self._client = anthropic.Anthropic(api_key=self.cfg.llm.anthropic_api_key)

    def fetch_rss_headlines(self, ticker: str) -> List[Dict[str, str]]:
        """Scrape public RSS feeds and filter for ticker mentions."""
        headlines = []
        for source, url in RSS_SOURCES.items():
            try:
                resp = self._http.get(url, headers={"User-Agent": "Mozilla/5.0"})
                if resp.status_code != 200:
                    continue
                root = ElementTree.fromstring(resp.content)
                for item in root.iter("item"):
                    title = item.findtext("title") or ""
                    desc = item.findtext("description") or ""
                    if ticker.upper() in title.upper() or ticker.upper() in desc.upper():
                        headlines.append({
                            "source": source,
                            "title": title[:200],
                            "description": desc[:300],
                        })
            except Exception as exc:
                logger.debug("RSS fetch failed for %s (%s): %s", source, ticker, exc)
        logger.info("Found %d RSS headlines for %s", len(headlines), ticker)
        return headlines

    def _llm_analyze(self, ticker: str, headlines: List[Dict]) -> Dict[str, Any]:
        if not self._client:
            return self._rule_based_sentiment(ticker, headlines)

        text = "\n".join(
            f"[{h['source']}] {h['title']}: {h.get('description', '')}"
            for h in headlines[:30]
        )
        user_msg = (
            f"Stock: {ticker}\n\n"
            f"Headlines & Summaries:\n{text or 'No headlines found.'}\n\n"
            "Analyze sentiment and respond as JSON."
        )
        try:
            msg = self._client.messages.create(
                model=self.cfg.llm.model,
                max_tokens=1024,
                system=SENTIMENT_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            )
            data = json.loads(msg.content[0].text.strip())
            logger.info("Sentiment LLM analysis complete for %s | %s", ticker, data.get("overall_sentiment"))
            return data
        except Exception as exc:
            logger.error("Sentiment LLM failed for %s: %s", ticker, exc)
            return self._rule_based_sentiment(ticker, headlines)

    def _rule_based_sentiment(self, ticker: str, headlines: List[Dict]) -> Dict[str, Any]:
        positive_words = {"growth", "profit", "record", "upgrade", "buy", "strong", "beat", "rally", "surge"}
        negative_words = {"loss", "decline", "downgrade", "sell", "fraud", "penalty", "cut", "miss", "fall", "crash"}
        hype_words = {"must buy", "multibagger", "10x", "guaranteed", "sure shot", "tip"}

        pos = neg = hype = 0
        for h in headlines:
            text = (h.get("title", "") + " " + h.get("description", "")).lower()
            pos += sum(1 for w in positive_words if w in text)
            neg += sum(1 for w in negative_words if w in text)
            hype += sum(1 for w in hype_words if w in text)

        if pos > neg * 1.5:
            sentiment = "Bullish"
            score = 7.0
        elif neg > pos * 1.5:
            sentiment = "Bearish"
            score = 3.0
        elif pos > 0 or neg > 0:
            sentiment = "Mixed"
            score = 5.0
        else:
            sentiment = "Neutral"
            score = 5.0

        return {
            "overall_sentiment": sentiment,
            "hype_detected": hype > 2,
            "fear_detected": neg > pos * 2,
            "accumulation_signal": False,
            "retail_buzz_level": "High" if len(headlines) > 10 else ("Medium" if headlines else "Low"),
            "analyst_bias": "Positive" if pos > neg else ("Negative" if neg > pos else "Neutral"),
            "sentiment_score": score,
            "key_signals": [f"{len(headlines)} headlines found, keyword sentiment: {sentiment}"],
            "contrarian_note": "LLM not configured — rule-based only.",
        }

    def analyze(self, ticker: str, extra_articles: Optional[List[Dict]] = None) -> Dict[str, Any]:
        logger.info("Sentiment analysis for %s", ticker)
        rss_headlines = self.fetch_rss_headlines(ticker)
        all_headlines = rss_headlines + (extra_articles or [])

        result = self._llm_analyze(ticker, all_headlines)
        result["ticker"] = ticker
        result["headline_count"] = len(all_headlines)
        return result

    def close(self):
        self._http.close()
