"""
Broker Factory — Strategy pattern for picking a broker connector at runtime.

Each connector module (zerodha.py, upstox.py, angelone.py, dhan.py) self-registers
via `@BrokerFactory.register("name")`. BrokerAgent looks up the active connector by
config.broker.active_broker (config/default.yaml, overridable via ACTIVE_BROKER env
var) instead of hardcoding a single broker — this is what lets live orders actually
route to whichever broker the user configured, and lets a new broker be added by
writing one connector file + registering it, no BrokerAgent edit required.
"""
from typing import Dict, Type


class BrokerFactory:
    _connectors: Dict[str, Type] = {}

    @classmethod
    def register(cls, name: str):
        def decorator(connector_cls: Type) -> Type:
            cls._connectors[name] = connector_cls
            return connector_cls
        return decorator

    @classmethod
    def create(cls, name: str, broker_config):
        try:
            connector_cls = cls._connectors[name]
        except KeyError:
            raise ValueError(
                f"Unknown broker {name!r}. Registered brokers: {sorted(cls._connectors)}"
            )
        return connector_cls(broker_config)

    @classmethod
    def available(cls) -> list:
        return sorted(cls._connectors)
