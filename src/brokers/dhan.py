"""DhanHQ API broker integration."""
from typing import Any, Dict

from src.brokers.base import BrokerConnector
from src.brokers.factory import BrokerFactory
from src.utils.logger import get_logger

logger = get_logger(__name__)


@BrokerFactory.register("dhan")
class DhanConnector(BrokerConnector):
    """
    Wraps the DhanHQ Python SDK.
    Requires: pip install dhanhq
    API docs: https://dhanhq.co/docs/v2/
    """

    def __init__(self, broker_config):
        super().__init__(broker_config)
        self.client_id = broker_config.dhan_client_id
        self.access_token = broker_config.dhan_access_token

    def _get_client(self):
        try:
            from dhanhq import dhanhq
            return dhanhq(self.client_id, self.access_token)
        except ImportError:
            raise RuntimeError("dhanhq not installed. Run: pip install dhanhq")

    def place_order(self, order_request) -> Dict[str, Any]:
        try:
            dhan = self._get_client()
            resp = dhan.place_order(
                security_id="",  # fill from Dhan scrip master
                exchange_segment=dhan.NSE,
                transaction_type=dhan.BUY if order_request.side == "BUY" else dhan.SELL,
                quantity=order_request.quantity,
                order_type=dhan.LIMIT if order_request.price else dhan.MARKET,
                product_type=dhan.CNC,
                price=order_request.price or 0,
            )
            logger.info("DhanHQ order placed | %s", resp)
            return {"status": "COMPLETE", "order_id": resp.get("data", {}).get("orderId"), "broker": "dhan"}
        except Exception as exc:
            logger.error("DhanHQ order failed: %s", exc)
            return {"status": "ERROR", "reason": str(exc)}

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        try:
            dhan = self._get_client()
            dhan.cancel_order(order_id)
            return {"status": "CANCELLED", "order_id": order_id}
        except Exception as exc:
            return {"status": "ERROR", "reason": str(exc)}
