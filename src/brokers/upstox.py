"""Upstox API v2 broker integration."""
from typing import Any, Dict

from src.brokers.base import BrokerConnector
from src.brokers.factory import BrokerFactory
from src.utils.logger import get_logger

logger = get_logger(__name__)


@BrokerFactory.register("upstox")
class UpstoxConnector(BrokerConnector):
    """
    Wraps the Upstox Python SDK v2.
    Requires: pip install upstox-python-sdk
    API docs: https://upstox.com/developer/api-documentation/
    """

    def __init__(self, broker_config):
        super().__init__(broker_config)
        self.api_key = broker_config.upstox_api_key
        self.api_secret = broker_config.upstox_api_secret
        self._access_token: str = ""

    def set_access_token(self, token: str):
        self._access_token = token
        logger.info("Upstox access token set")

    def place_order(self, order_request) -> Dict[str, Any]:
        try:
            import upstox_client
            configuration = upstox_client.Configuration()
            configuration.access_token = self._access_token
            api = upstox_client.OrderApi(upstox_client.ApiClient(configuration))
            body = upstox_client.PlaceOrderRequest(
                quantity=order_request.quantity,
                product="D",  # Delivery
                validity="DAY",
                price=order_request.price or 0,
                tag="investment-agent",
                instrument_token=f"NSE_EQ|{order_request.ticker}",
                order_type="LIMIT" if order_request.price else "MARKET",
                transaction_type=order_request.side,
                disclosed_quantity=0,
                trigger_price=0,
                is_amo=False,
            )
            resp = api.place_order(body, "2.0")
            logger.info("Upstox order placed | order_id=%s", resp.data.order_id)
            return {"status": "COMPLETE", "order_id": resp.data.order_id, "broker": "upstox"}
        except ImportError:
            return {"status": "ERROR", "reason": "upstox-python-sdk not installed"}
        except Exception as exc:
            logger.error("Upstox order failed: %s", exc)
            return {"status": "ERROR", "reason": str(exc)}

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        try:
            import upstox_client
            configuration = upstox_client.Configuration()
            configuration.access_token = self._access_token
            api = upstox_client.OrderApi(upstox_client.ApiClient(configuration))
            api.cancel_order(order_id, "2.0")
            return {"status": "CANCELLED", "order_id": order_id}
        except Exception as exc:
            return {"status": "ERROR", "reason": str(exc)}
