"""Broker Strategy interface — every broker connector implements this."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BrokerConnector(ABC):
    """Common interface for all broker connectors (Zerodha, Upstox, Angel One, DhanHQ, ...)."""

    def __init__(self, broker_config):
        self.broker_config = broker_config

    @abstractmethod
    def place_order(self, order_request) -> Dict[str, Any]:
        ...

    @abstractmethod
    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        ...

    def get_holdings(self) -> List[Any]:
        raise NotImplementedError(f"{type(self).__name__} does not support get_holdings")

    def get_positions(self) -> Dict[str, Any]:
        raise NotImplementedError(f"{type(self).__name__} does not support get_positions")
