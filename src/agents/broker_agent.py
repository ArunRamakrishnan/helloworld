"""Broker Execution Agent — paper trading by default; real orders require explicit user confirmation."""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.validators import validate_price, validate_quantity, validate_ticker

logger = get_logger(__name__)

DISCLAIMER = (
    "This is educational research, not financial advice. "
    "Consult a SEBI-registered investment adviser before investing."
)


class OrderRequest:
    def __init__(
        self,
        ticker: str,
        side: str,
        quantity: int,
        price: Optional[float],
        order_type: str = "LIMIT",
        rationale: str = "",
    ):
        self.ticker = validate_ticker(ticker)
        self.side = side.upper()
        self.quantity = validate_quantity(quantity)
        self.price = validate_price(price) if price else None
        self.order_type = order_type.upper()
        self.rationale = rationale
        self.request_id = str(uuid.uuid4())

    def preview(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "ticker": self.ticker,
            "side": self.side,
            "quantity": self.quantity,
            "price": self.price,
            "order_type": self.order_type,
            "estimated_value": (self.quantity * self.price) if self.price else None,
            "rationale": self.rationale,
        }


class PaperTradingLog:
    """In-memory paper trading log (in production, persisted to DB via OrderRepository)."""

    def __init__(self):
        self._orders: List[Dict[str, Any]] = []

    def record(self, order_request: OrderRequest, status: str = "COMPLETE") -> Dict[str, Any]:
        entry = {
            **order_request.preview(),
            "is_paper_trade": True,
            "status": status,
            "executed_at": datetime.utcnow().isoformat(),
        }
        self._orders.append(entry)
        logger.info("PAPER TRADE | %s %d %s @ %s", order_request.side, order_request.quantity, order_request.ticker, order_request.price)
        return entry

    def list_orders(self) -> List[Dict[str, Any]]:
        return list(self._orders)


class BrokerAgent:
    """
    Manages all order execution.

    Default mode: PAPER TRADING.
    Live trading requires:
    1. PAPER_TRADING=false in .env
    2. Valid broker API credentials in .env
    3. Explicit user_confirmed=True flag on every order
    """

    def __init__(self, config=None):
        self.cfg = config or get_config()
        self.paper_log = PaperTradingLog()
        self._broker_client = None  # loaded lazily

        if not self.cfg.paper_trading:
            logger.warning(
                "LIVE TRADING MODE is enabled. All orders will be sent to the broker. "
                "Every order requires explicit user confirmation."
            )

    @property
    def is_paper_trading(self) -> bool:
        return self.cfg.paper_trading

    def preview_order(self, order_request: OrderRequest) -> Dict[str, Any]:
        """Returns the order preview and risk warnings — must be shown to user before execution."""
        preview = order_request.preview()
        preview["mode"] = "PAPER TRADE" if self.is_paper_trading else "LIVE ORDER — REAL MONEY"
        preview["risk_warning"] = (
            "This will use real funds from your broker account. Losses are possible."
            if not self.is_paper_trading
            else "This is a simulated paper trade. No real money involved."
        )
        preview["disclaimer"] = DISCLAIMER
        return preview

    def place_order(
        self,
        order_request: OrderRequest,
        user_confirmed: bool = False,
        available_funds: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Place an order (paper or live).

        Args:
            order_request: The order to place
            user_confirmed: Must be True for any order execution
            available_funds: Used to validate the order doesn't exceed available capital
        """
        if not user_confirmed:
            return {
                "status": "REJECTED",
                "reason": "User confirmation is required before placing any order.",
                "preview": self.preview_order(order_request),
                "disclaimer": DISCLAIMER,
            }

        # Funds check
        if available_funds is not None and order_request.price:
            required = order_request.quantity * order_request.price
            if required > available_funds:
                return {
                    "status": "REJECTED",
                    "reason": f"Insufficient funds. Required: ₹{required:,.2f}, Available: ₹{available_funds:,.2f}",
                    "disclaimer": DISCLAIMER,
                }

        if self.is_paper_trading:
            return self.paper_log.record(order_request)

        # Live order path — broker API call
        return self._place_live_order(order_request)

    def _place_live_order(self, order_request: OrderRequest) -> Dict[str, Any]:
        """Dispatches to the configured broker connector."""
        broker_key = self.cfg.broker.zerodha_api_key
        if not broker_key:
            return {
                "status": "REJECTED",
                "reason": "No broker API key configured. Set ZERODHA_API_KEY (or equivalent) in .env.",
            }
        # Import the appropriate broker module
        try:
            from src.brokers.zerodha import ZerodhaConnector
            connector = ZerodhaConnector(self.cfg.broker)
            result = connector.place_order(order_request)
            logger.info("LIVE ORDER placed | id=%s | status=%s", result.get("order_id"), result.get("status"))
            return result
        except Exception as exc:
            logger.error("Live order failed for %s: %s", order_request.ticker, exc)
            return {"status": "ERROR", "reason": str(exc)}

    def cancel_order(self, order_id: str, user_confirmed: bool = False) -> Dict[str, Any]:
        if not user_confirmed:
            return {"status": "REJECTED", "reason": "User confirmation required to cancel orders."}
        if self.is_paper_trading:
            return {"status": "CANCELLED", "order_id": order_id, "mode": "PAPER TRADE"}
        try:
            from src.brokers.zerodha import ZerodhaConnector
            connector = ZerodhaConnector(self.cfg.broker)
            return connector.cancel_order(order_id)
        except Exception as exc:
            return {"status": "ERROR", "reason": str(exc)}

    def get_paper_trade_log(self) -> List[Dict[str, Any]]:
        return self.paper_log.list_orders()
