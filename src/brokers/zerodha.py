"""Zerodha Kite Connect broker integration."""
from typing import Any, Dict, Optional

from src.brokers.base import BrokerConnector
from src.brokers.factory import BrokerFactory
from src.utils.logger import get_logger

logger = get_logger(__name__)


@BrokerFactory.register("zerodha")
class ZerodhaConnector(BrokerConnector):
    """
    Wraps the Kite Connect Python SDK.
    Requires: pip install kiteconnect
    API docs: https://kite.trade/docs/connect/v3/
    """

    def __init__(self, broker_config):
        super().__init__(broker_config)
        self.api_key = broker_config.zerodha_api_key
        self.api_secret = broker_config.zerodha_api_secret
        self._kite = None

    def _get_client(self):
        if self._kite is not None:
            return self._kite
        try:
            from kiteconnect import KiteConnect
            self._kite = KiteConnect(api_key=self.api_key)
            return self._kite
        except ImportError:
            raise RuntimeError("kiteconnect not installed. Run: pip install kiteconnect")

    def generate_session(self, request_token: str) -> str:
        """Exchange request_token for access_token. Call once per login."""
        kite = self._get_client()
        data = kite.generate_session(request_token, api_secret=self.api_secret)
        access_token = data["access_token"]
        kite.set_access_token(access_token)
        logger.info("Zerodha session established")
        return access_token

    def set_access_token(self, access_token: str):
        kite = self._get_client()
        kite.set_access_token(access_token)

    def place_order(self, order_request) -> Dict[str, Any]:
        kite = self._get_client()
        try:
            order_id = kite.place_order(
                tradingsymbol=order_request.ticker,
                exchange=kite.EXCHANGE_NSE,
                transaction_type=kite.TRANSACTION_TYPE_BUY if order_request.side == "BUY" else kite.TRANSACTION_TYPE_SELL,
                quantity=order_request.quantity,
                order_type=kite.ORDER_TYPE_LIMIT if order_request.order_type == "LIMIT" else kite.ORDER_TYPE_MARKET,
                price=order_request.price,
                product=kite.PRODUCT_CNC,
                variety=kite.VARIETY_REGULAR,
            )
            logger.info("Zerodha order placed | order_id=%s", order_id)
            return {"status": "COMPLETE", "order_id": str(order_id), "broker": "zerodha"}
        except Exception as exc:
            logger.error("Zerodha order failed: %s", exc)
            return {"status": "ERROR", "reason": str(exc)}

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        kite = self._get_client()
        try:
            kite.cancel_order(variety=kite.VARIETY_REGULAR, order_id=order_id)
            return {"status": "CANCELLED", "order_id": order_id}
        except Exception as exc:
            return {"status": "ERROR", "reason": str(exc)}

    def get_holdings(self) -> list:
        return self._get_client().holdings()

    def get_positions(self) -> Dict[str, Any]:
        return self._get_client().positions()
