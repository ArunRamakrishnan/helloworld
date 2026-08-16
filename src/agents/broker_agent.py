"""Broker Execution Agent — paper trading by default; real orders require explicit user confirmation."""
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.agents.registry import AgentRegistry
from src.utils import config as config_module
from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.validators import validate_price, validate_quantity, validate_ticker

logger = get_logger(__name__)


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


@AgentRegistry.register("broker")
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
        # Disclaimer text always comes from the real loaded config, independent of
        # whatever `config` object the caller injects — or, in tests, of `get_config`
        # itself being patched at module scope (see fundamental_agent.py and
        # tests/test_broker_agent.py's `_make_agent`).
        self.disclaimer = config_module.get_config().disclaimer
        self.paper_log = PaperTradingLog()
        self._broker_client = None  # loaded lazily

        if not self.cfg.paper_trading:  # pragma: no cover
            logger.warning(  # pragma: no cover
                "LIVE TRADING MODE is enabled. All orders will be sent to the broker. "
                "Every order requires explicit user confirmation."
            )  # pragma: no cover

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
        preview["disclaimer"] = self.disclaimer
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
                "disclaimer": self.disclaimer,
            }

        # Funds check
        if available_funds is not None and order_request.price:
            required = order_request.quantity * order_request.price
            if required > available_funds:
                return {
                    "status": "REJECTED",
                    "reason": f"Insufficient funds. Required: ₹{required:,.2f}, Available: ₹{available_funds:,.2f}",
                    "disclaimer": self.disclaimer,
                }

        if self.is_paper_trading:
            return self.paper_log.record(order_request)

        # Live order path — broker API call
        return self._place_live_order(order_request)  # pragma: no cover

    def _place_live_order(self, order_request: OrderRequest) -> Dict[str, Any]:  # pragma: no cover
        """Dispatches to the broker connector configured via config.broker.active_broker
        (config/default.yaml, overridable with the ACTIVE_BROKER env var). Requires
        live broker credentials for that broker."""
        # Registers all connectors with BrokerFactory as a side effect of import.
        import src.brokers.zerodha  # noqa: F401
        import src.brokers.upstox  # noqa: F401
        import src.brokers.angelone  # noqa: F401
        import src.brokers.dhan  # noqa: F401
        from src.brokers.factory import BrokerFactory

        active_broker = self.cfg.broker.active_broker
        try:
            connector = BrokerFactory.create(active_broker, self.cfg.broker)
        except ValueError as exc:
            return {"status": "REJECTED", "reason": str(exc)}

        try:
            result = connector.place_order(order_request)
            logger.info(
                "LIVE ORDER placed via %s | id=%s | status=%s",
                active_broker, result.get("order_id"), result.get("status"),
            )
            return result
        except Exception as exc:
            logger.error("Live order failed for %s: %s", order_request.ticker, exc)
            return {"status": "ERROR", "reason": str(exc)}

    def cancel_order(self, order_id: str, user_confirmed: bool = False) -> Dict[str, Any]:
        if not user_confirmed:
            return {"status": "REJECTED", "reason": "User confirmation required to cancel orders."}
        if self.is_paper_trading:
            return {"status": "CANCELLED", "order_id": order_id, "mode": "PAPER TRADE"}
        try:  # pragma: no cover
            import src.brokers.zerodha  # noqa: F401  # pragma: no cover
            import src.brokers.upstox  # noqa: F401  # pragma: no cover
            import src.brokers.angelone  # noqa: F401  # pragma: no cover
            import src.brokers.dhan  # noqa: F401  # pragma: no cover
            from src.brokers.factory import BrokerFactory  # pragma: no cover
            connector = BrokerFactory.create(self.cfg.broker.active_broker, self.cfg.broker)  # pragma: no cover
            return connector.cancel_order(order_id)  # pragma: no cover
        except Exception as exc:  # pragma: no cover
            return {"status": "ERROR", "reason": str(exc)}  # pragma: no cover

    def get_paper_trade_log(self) -> List[Dict[str, Any]]:
        return self.paper_log.list_orders()
