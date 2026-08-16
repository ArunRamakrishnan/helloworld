"""Unit tests for BrokerFactory (Strategy/Factory pattern for broker connectors)."""
import pytest

# Importing these modules registers their connector classes as a side effect.
import src.brokers.zerodha  # noqa: F401
import src.brokers.upstox  # noqa: F401
import src.brokers.angelone  # noqa: F401
import src.brokers.dhan  # noqa: F401
from src.brokers.base import BrokerConnector
from src.brokers.factory import BrokerFactory
from src.brokers.zerodha import ZerodhaConnector
from src.brokers.upstox import UpstoxConnector
from src.brokers.angelone import AngelOneConnector
from src.brokers.dhan import DhanConnector
from src.utils.config import BrokerConfig


class TestBrokerFactory:
    def test_all_four_brokers_registered(self):
        assert set(BrokerFactory.available()) == {"zerodha", "upstox", "angelone", "dhan"}

    @pytest.mark.parametrize("name,expected_cls", [
        ("zerodha", ZerodhaConnector),
        ("upstox", UpstoxConnector),
        ("angelone", AngelOneConnector),
        ("dhan", DhanConnector),
    ])
    def test_create_returns_correct_connector_type(self, name, expected_cls):
        connector = BrokerFactory.create(name, BrokerConfig())
        assert isinstance(connector, expected_cls)

    def test_create_unknown_broker_raises_value_error(self):
        with pytest.raises(ValueError):
            BrokerFactory.create("not_a_real_broker", BrokerConfig())

    def test_all_connectors_are_broker_connector_subclasses(self):
        for name in BrokerFactory.available():
            connector = BrokerFactory.create(name, BrokerConfig())
            assert isinstance(connector, BrokerConnector)

    def test_connector_carries_credentials_from_broker_config(self):
        cfg = BrokerConfig(zerodha_api_key="key123", zerodha_api_secret="secret456")
        connector = BrokerFactory.create("zerodha", cfg)
        assert connector.api_key == "key123"
        assert connector.api_secret == "secret456"

    def test_unimplemented_holdings_raises_not_implemented(self):
        # Upstox/AngelOne/Dhan don't implement get_holdings/get_positions —
        # BrokerConnector's default should raise a clear error, not AttributeError.
        connector = BrokerFactory.create("upstox", BrokerConfig())
        with pytest.raises(NotImplementedError):
            connector.get_holdings()
