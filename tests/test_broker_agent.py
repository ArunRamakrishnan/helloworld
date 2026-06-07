"""Unit tests for BrokerAgent — paper trading, order validation, confirmation gate."""
import pytest
from unittest.mock import patch, MagicMock

from src.agents.broker_agent import BrokerAgent, OrderRequest
from src.utils.validators import validate_ticker, validate_quantity, validate_price


# ------------------------------------------------------------------
# OrderRequest validation
# ------------------------------------------------------------------

class TestOrderRequest:
    def test_valid_order_request(self):
        req = OrderRequest("RELIANCE", "BUY", 10, 2850.0)
        assert req.ticker == "RELIANCE"
        assert req.side == "BUY"
        assert req.quantity == 10
        assert req.price == pytest.approx(2850.0)

    def test_ticker_normalised_to_uppercase(self):
        req = OrderRequest("reliance", "BUY", 5, 100.0)
        assert req.ticker == "RELIANCE"

    def test_invalid_ticker_raises(self):
        with pytest.raises(ValueError):
            OrderRequest("", "BUY", 5, 100.0)

    def test_invalid_quantity_raises(self):
        with pytest.raises(ValueError):
            OrderRequest("INFY", "BUY", -1, 100.0)

    def test_zero_quantity_raises(self):
        with pytest.raises(ValueError):
            OrderRequest("INFY", "BUY", 0, 100.0)

    def test_negative_price_raises(self):
        with pytest.raises(ValueError):
            OrderRequest("INFY", "BUY", 5, -100.0)

    def test_preview_contains_all_fields(self):
        req = OrderRequest("TCS", "SELL", 2, 3500.0, rationale="Taking profits")
        preview = req.preview()
        for key in ["ticker", "side", "quantity", "price", "order_type", "estimated_value", "rationale", "request_id"]:
            assert key in preview

    def test_preview_estimated_value_correct(self):
        req = OrderRequest("HDFC", "BUY", 5, 1500.0)
        assert req.preview()["estimated_value"] == pytest.approx(7500.0)


# ------------------------------------------------------------------
# BrokerAgent — paper trading (default)
# ------------------------------------------------------------------

class TestBrokerAgentPaperTrading:
    def _make_agent(self):
        with patch("src.agents.broker_agent.get_config") as mock_cfg:
            mock_cfg.return_value = MagicMock(paper_trading=True, broker=MagicMock())
            return BrokerAgent()

    def test_is_paper_trading_by_default(self):
        agent = self._make_agent()
        assert agent.is_paper_trading is True

    def test_order_rejected_without_confirmation(self):
        agent = self._make_agent()
        req = OrderRequest("INFY", "BUY", 10, 1400.0)
        result = agent.place_order(req, user_confirmed=False)
        assert result["status"] == "REJECTED"
        assert "confirmation" in result["reason"].lower()

    def test_paper_order_placed_with_confirmation(self):
        agent = self._make_agent()
        req = OrderRequest("WIPRO", "BUY", 20, 450.0)
        result = agent.place_order(req, user_confirmed=True)
        assert result["status"] == "COMPLETE"
        assert result["is_paper_trade"] is True

    def test_insufficient_funds_rejected(self):
        agent = self._make_agent()
        req = OrderRequest("RELIANCE", "BUY", 100, 3000.0)  # 3,00,000 required
        result = agent.place_order(req, user_confirmed=True, available_funds=50000.0)
        assert result["status"] == "REJECTED"
        assert "Insufficient" in result["reason"]

    def test_paper_trade_log_records_order(self):
        agent = self._make_agent()
        req = OrderRequest("TCS", "BUY", 5, 3500.0)
        agent.place_order(req, user_confirmed=True)
        log = agent.get_paper_trade_log()
        assert len(log) == 1
        assert log[0]["ticker"] == "TCS"

    def test_multiple_orders_in_log(self):
        agent = self._make_agent()
        for i in range(3):
            req = OrderRequest("INFY", "BUY", i + 1, 1400.0)
            agent.place_order(req, user_confirmed=True)
        assert len(agent.get_paper_trade_log()) == 3

    def test_preview_shows_paper_trade_mode(self):
        agent = self._make_agent()
        req = OrderRequest("HDFCBANK", "BUY", 1, 1600.0)
        preview = agent.preview_order(req)
        assert "PAPER" in preview["mode"]
        assert "disclaimer" in preview

    def test_cancel_paper_trade_with_confirmation(self):
        agent = self._make_agent()
        result = agent.cancel_order("fake-order-123", user_confirmed=True)
        assert result["status"] == "CANCELLED"

    def test_cancel_without_confirmation_rejected(self):
        agent = self._make_agent()
        result = agent.cancel_order("fake-order-123", user_confirmed=False)
        assert result["status"] == "REJECTED"

    def test_disclaimer_always_in_preview(self):
        agent = self._make_agent()
        req = OrderRequest("SBIN", "SELL", 50, 600.0)
        preview = agent.preview_order(req)
        assert "disclaimer" in preview
        assert "SEBI" in preview["disclaimer"]
