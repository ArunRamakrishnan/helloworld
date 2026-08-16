"""Angel One SmartAPI broker integration."""
from typing import Any, Dict

from src.brokers.base import BrokerConnector
from src.brokers.factory import BrokerFactory
from src.utils.logger import get_logger

logger = get_logger(__name__)


@BrokerFactory.register("angelone")
class AngelOneConnector(BrokerConnector):
    """
    Wraps the Angel One SmartAPI Python library.
    Requires: pip install smartapi-python
    API docs: https://smartapi.angelbroking.com/
    """

    def __init__(self, broker_config):
        super().__init__(broker_config)
        self.api_key = broker_config.angel_api_key
        self.client_id = broker_config.angel_client_id
        self._smart_api = None

    def _get_client(self, totp: str, password: str):
        try:
            from SmartApi import SmartConnect
            obj = SmartConnect(api_key=self.api_key)
            obj.generateSession(self.client_id, password, totp)
            self._smart_api = obj
            return obj
        except ImportError:
            raise RuntimeError("smartapi-python not installed. Run: pip install smartapi-python")

    def place_order(self, order_request) -> Dict[str, Any]:
        if not self._smart_api:
            return {"status": "ERROR", "reason": "Angel One session not established. Call _get_client first."}
        try:
            order_params = {
                "variety": "NORMAL",
                "tradingsymbol": order_request.ticker,
                "symboltoken": "",  # must be filled from symbol master
                "transactiontype": order_request.side,
                "exchange": "NSE",
                "ordertype": "LIMIT" if order_request.price else "MARKET",
                "producttype": "DELIVERY",
                "duration": "DAY",
                "price": str(order_request.price or 0),
                "squareoff": "0",
                "stoploss": "0",
                "quantity": str(order_request.quantity),
            }
            resp = self._smart_api.placeOrder(order_params)
            logger.info("Angel One order placed | %s", resp)
            return {"status": "COMPLETE", "order_id": resp.get("data", {}).get("orderid"), "broker": "angelone"}
        except Exception as exc:
            logger.error("Angel One order failed: %s", exc)
            return {"status": "ERROR", "reason": str(exc)}

    def cancel_order(self, order_id: str, variety: str = "NORMAL") -> Dict[str, Any]:
        if not self._smart_api:
            return {"status": "ERROR", "reason": "Session not established"}
        try:
            self._smart_api.cancelOrder(order_id, variety)
            return {"status": "CANCELLED", "order_id": order_id}
        except Exception as exc:
            return {"status": "ERROR", "reason": str(exc)}
