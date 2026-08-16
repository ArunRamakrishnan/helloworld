"""
Agent registry — Strategy/Factory pattern for agent instantiation and pipeline wiring.

Every agent class self-registers with `@AgentRegistry.register("name")`. The
orchestrator's enrichment pipeline (see orchestrator.py) reads the ordered list of
names in config.pipeline.enabled_agents and looks each one up here instead of
hardcoding imports and `self.xxx_agent = XxxAgent(...)` assignments.

To add a brand-new enrichment agent to the research pipeline:
  1. Write the agent class with an `analyze(ticker, **kwargs)` method.
  2. Give it an `output_key` class attribute and a `pipeline_kwargs(ticker, context)`
     staticmethod that pulls whatever inputs it needs out of the shared context dict.
  3. Decorate the class with `@AgentRegistry.register("your_name")`.
  4. Add "your_name" to config.pipeline.enabled_agents in config/default.yaml.
No orchestrator.py edit is required.
"""
from typing import Dict, Type


class AgentRegistry:
    _agents: Dict[str, Type] = {}

    @classmethod
    def register(cls, name: str):
        def decorator(agent_cls: Type) -> Type:
            cls._agents[name] = agent_cls
            return agent_cls
        return decorator

    @classmethod
    def get(cls, name: str) -> Type:
        try:
            return cls._agents[name]
        except KeyError:
            raise KeyError(
                f"No agent registered as {name!r}. Registered agents: {sorted(cls._agents)}"
            )

    @classmethod
    def create(cls, name: str, config=None):
        return cls.get(name)(config=config)

    @classmethod
    def available(cls) -> list:
        return sorted(cls._agents)
