"""Unit tests for MoatAgent and NewsAgent — mocked LLM calls."""
import json
import pytest
from unittest.mock import MagicMock, patch

from src.agents.moat_agent import MoatAgent, MOAT_DIMENSIONS
from src.agents.news_agent import NewsAgent


# ------------------------------------------------------------------
# MoatAgent
# ------------------------------------------------------------------

def _make_moat_agent(with_llm=False):
    cfg = MagicMock()
    cfg.llm.anthropic_api_key = "fake-key" if with_llm else None
    cfg.llm.model = "claude-opus-4-8"
    return MoatAgent(config=cfg)


class TestMoatAgent:
    def test_fallback_score_returns_all_dimensions(self):
        agent = _make_moat_agent(with_llm=False)
        result = agent._fallback_score("TEST")
        for dim in MOAT_DIMENSIONS:
            assert dim in result

    def test_fallback_score_is_5_for_all(self):
        agent = _make_moat_agent(with_llm=False)
        result = agent._fallback_score("TEST")
        for dim in MOAT_DIMENSIONS:
            assert result[dim] == 5.0

    def test_overall_moat_score_in_range(self):
        agent = _make_moat_agent(with_llm=False)
        scores = {dim: 7.0 for dim in MOAT_DIMENSIONS}
        score = agent.overall_moat_score(scores)
        assert 0 <= score <= 10

    def test_overall_moat_score_max_inputs_gives_near_10(self):
        agent = _make_moat_agent(with_llm=False)
        scores = {dim: 10.0 for dim in MOAT_DIMENSIONS}
        score = agent.overall_moat_score(scores)
        assert score == pytest.approx(10.0)

    def test_overall_moat_score_min_inputs_gives_0(self):
        agent = _make_moat_agent(with_llm=False)
        scores = {dim: 0.0 for dim in MOAT_DIMENSIONS}
        score = agent.overall_moat_score(scores)
        assert score == pytest.approx(0.0)

    def test_analyze_without_llm_uses_fallback(self):
        agent = _make_moat_agent(with_llm=False)
        result = agent.analyze("HDFC", "HDFC is a leading private sector bank in India.")
        assert "moat_score" in result
        assert "dimension_scores" in result
        assert 0 <= result["moat_score"] <= 10

    def test_analyze_with_llm_success(self):
        agent = _make_moat_agent(with_llm=True)
        llm_response = {dim: 8.0 for dim in MOAT_DIMENSIONS}
        llm_response["summary"] = "Strong moat with high switching costs."
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text=json.dumps(llm_response))]
        agent._client.messages.create = MagicMock(return_value=mock_msg)

        result = agent.analyze("TCS", "TCS is a global IT services company.")
        assert result["moat_score"] == pytest.approx(8.0, abs=0.5)
        assert "Strong moat" in result["moat_summary"]

    def test_analyze_with_llm_fallback_on_error(self):
        agent = _make_moat_agent(with_llm=True)
        agent._client.messages.create = MagicMock(side_effect=Exception("API error"))
        result = agent.analyze("WIPRO", "Wipro is an IT company.")
        assert "moat_score" in result  # graceful fallback

    def test_analyze_returns_ticker(self):
        agent = _make_moat_agent(with_llm=False)
        result = agent.analyze("INFY", "Infosys provides IT services.")
        assert result["ticker"] == "INFY"


# ------------------------------------------------------------------
# NewsAgent
# ------------------------------------------------------------------

def _make_news_agent(with_llm=False):
    cfg = MagicMock()
    cfg.llm.anthropic_api_key = "fake-key" if with_llm else None
    cfg.llm.model = "claude-opus-4-8"
    return NewsAgent(config=cfg)

SAMPLE_ARTICLES = [
    {"title": "Reliance posts record Q4 profit", "source": "ET", "published_at": "2026-06-01", "description": "Net profit up 20%"},
    {"title": "Reliance JIO 5G expansion", "source": "Mint", "published_at": "2026-06-02", "description": "New cities added"},
]


class TestNewsAgent:
    def test_analyze_empty_articles_returns_neutral(self):
        agent = _make_news_agent(with_llm=False)
        result = agent.analyze("RELIANCE", [])
        assert result["sentiment"] == "Neutral"
        assert result["ticker"] == "RELIANCE"

    def test_keyword_fallback_positive_sentiment(self):
        agent = _make_news_agent(with_llm=False)
        articles = [{"title": "Strong profit growth record beat", "source": "ET", "published_at": "2026-06-01", "description": ""}]
        result = agent._keyword_fallback("TCS", articles)
        assert result["sentiment"] == "Positive"

    def test_keyword_fallback_negative_sentiment(self):
        agent = _make_news_agent(with_llm=False)
        articles = [{"title": "Loss decline fraud penalty", "source": "ET", "published_at": "2026-06-01", "description": ""}]
        result = agent._keyword_fallback("BAD", articles)
        assert result["sentiment"] == "Negative"

    def test_keyword_fallback_mixed_sentiment(self):
        agent = _make_news_agent(with_llm=False)
        articles = [{"title": "strong growth but also loss miss", "source": "ET", "published_at": "2026-06-01", "description": ""}]
        result = agent._keyword_fallback("MIX", articles)
        assert result["sentiment"] == "Mixed"

    def test_analyze_without_llm_uses_keyword_fallback(self):
        agent = _make_news_agent(with_llm=False)
        result = agent.analyze("RELIANCE", SAMPLE_ARTICLES)
        assert "sentiment" in result
        assert "summary" in result
        assert result["ticker"] == "RELIANCE"

    def test_analyze_with_llm_success(self):
        agent = _make_news_agent(with_llm=True)
        llm_response = {
            "summary": "Reliance reported strong Q4 results.",
            "sentiment": "Positive",
            "key_facts": ["Profit up 20%"],
            "unverified_claims": [],
            "warnings": [],
        }
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(text=json.dumps(llm_response))]
        agent._client.messages.create = MagicMock(return_value=mock_msg)

        result = agent.analyze("RELIANCE", SAMPLE_ARTICLES)
        assert result["sentiment"] == "Positive"
        assert "Profit up 20%" in result["key_facts"]

    def test_analyze_with_llm_fallback_on_error(self):
        agent = _make_news_agent(with_llm=True)
        agent._client.messages.create = MagicMock(side_effect=Exception("LLM down"))
        result = agent.analyze("TCS", SAMPLE_ARTICLES)
        assert "sentiment" in result  # graceful fallback

    def test_format_articles_caps_at_20(self):
        agent = _make_news_agent(with_llm=False)
        articles = [{"title": f"News {i}", "source": "ET", "published_at": "2026-06-01", "description": ""} for i in range(30)]
        formatted = agent._format_articles(articles)
        lines = [l for l in formatted.split("\n") if l.strip()]
        assert len(lines) <= 20
