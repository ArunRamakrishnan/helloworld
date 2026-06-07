"""Unit tests for DataCollectorAgent — mocked HTTP calls."""
import pytest
from unittest.mock import MagicMock, patch

from src.agents.data_collector import DataCollectorAgent


class TestDataCollectorAgent:
    def setup_method(self):
        cfg = MagicMock()
        cfg.news_api_key = "test-key"
        self.agent = DataCollectorAgent(config=cfg)

    def test_fetch_nse_stock_list_returns_list_on_success(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "data": [
                {"symbol": "RELIANCE", "meta": {"companyName": "Reliance Industries", "industry": "Energy"}},
                {"symbol": "TCS", "meta": {"companyName": "TCS", "industry": "IT"}},
            ]
        }
        self.agent._http.get = MagicMock(return_value=mock_resp)

        result = self.agent.fetch_nse_stock_list()
        assert len(result) == 2
        assert result[0]["ticker"] == "RELIANCE"
        assert result[0]["exchange"] == "NSE"

    def test_fetch_nse_stock_list_returns_empty_on_error(self):
        self.agent._http.get = MagicMock(side_effect=Exception("network error"))
        result = self.agent.fetch_nse_stock_list()
        assert result == []

    def test_fetch_nse_stock_list_stores_source_url(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "data": [{"symbol": "INFY", "meta": {"companyName": "Infosys", "industry": "IT"}}]
        }
        self.agent._http.get = MagicMock(return_value=mock_resp)
        result = self.agent.fetch_nse_stock_list()
        assert "source_url" in result[0]
        assert "fetched_at" in result[0]

    def test_fetch_news_returns_empty_when_no_api_key(self):
        cfg = MagicMock()
        cfg.news_api_key = None
        agent = DataCollectorAgent(config=cfg)
        result = agent.fetch_news("RELIANCE")
        assert result == []

    def test_fetch_news_returns_articles_on_success(self):
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {
            "articles": [
                {"title": "Reliance Q4 results", "source": {"name": "ET"}, "publishedAt": "2026-06-01", "url": "http://x.com/1", "description": "Strong results"},
                {"title": "Reliance JIO update", "source": {"name": "Mint"}, "publishedAt": "2026-06-02", "url": "http://x.com/2", "description": "5G expansion"},
            ]
        }
        self.agent._http.get = MagicMock(return_value=mock_resp)
        result = self.agent.fetch_news("RELIANCE")
        assert len(result) == 2
        assert result[0]["title"] == "Reliance Q4 results"

    def test_fetch_news_returns_empty_on_error(self):
        self.agent._http.get = MagicMock(side_effect=Exception("timeout"))
        result = self.agent.fetch_news("TCS")
        assert result == []

    def test_fetch_financials_screener_returns_ticker(self):
        result = self.agent.fetch_financials_screener("HDFC")
        assert result["ticker"] == "HDFC"

    def test_fetch_historical_prices_no_yfinance_returns_empty(self):
        with patch.dict("sys.modules", {"yfinance": None}):
            from datetime import date
            result = self.agent.fetch_historical_prices("RELIANCE", date(2024, 1, 1))
        assert result == []

    def test_close_does_not_raise(self):
        self.agent.close()  # should not throw

    def test_validate_ticker_in_fetch_financials(self):
        with pytest.raises(ValueError):
            self.agent.fetch_financials_screener("")
