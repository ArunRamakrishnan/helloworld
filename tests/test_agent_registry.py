"""Unit tests for the Agent Registry (Strategy/Factory pattern for pipeline agents)."""
import pytest

# Importing these modules registers their agent classes as a side effect.
import src.agents.fundamental_agent  # noqa: F401
import src.agents.valuation_agent  # noqa: F401
import src.agents.risk_agent  # noqa: F401
import src.agents.moat_agent  # noqa: F401
import src.agents.news_agent  # noqa: F401
import src.agents.sentiment_agent  # noqa: F401
import src.agents.fisher_agent  # noqa: F401
import src.agents.unicorn_detector  # noqa: F401
import src.agents.portfolio_agent  # noqa: F401
import src.agents.broker_agent  # noqa: F401
import src.agents.data_collector  # noqa: F401
import src.agents.audit_agent  # noqa: F401
from src.agents.registry import AgentRegistry
from src.agents.moat_agent import MoatAgent
from src.agents.fisher_agent import PhilipFisherAgent


class TestAgentRegistry:
    def test_all_expected_agents_registered(self):
        expected = {
            "fundamental", "valuation", "risk", "moat", "news", "sentiment",
            "fisher", "unicorn", "portfolio", "broker", "data_collector", "audit",
        }
        assert expected.issubset(set(AgentRegistry.available()))

    def test_get_returns_registered_class(self):
        assert AgentRegistry.get("moat") is MoatAgent

    def test_get_unknown_agent_raises(self):
        with pytest.raises(KeyError):
            AgentRegistry.get("does_not_exist")

    def test_create_instantiates_agent(self):
        agent = AgentRegistry.create("fisher")
        assert isinstance(agent, PhilipFisherAgent)

    def test_enrichment_agents_expose_output_key_and_pipeline_kwargs(self):
        for name in ("moat", "news", "sentiment", "fisher", "unicorn"):
            agent_cls = AgentRegistry.get(name)
            assert hasattr(agent_cls, "output_key")
            assert callable(getattr(agent_cls, "pipeline_kwargs"))

    def test_fisher_pipeline_kwargs_pulls_from_context(self):
        context = {
            "business_description": "desc",
            "revenue_cagr_3y": 0.2,
            "profit_cagr_3y": 0.15,
            "roe": 0.18,
        }
        kwargs = PhilipFisherAgent.pipeline_kwargs("TCS", context)
        assert kwargs == {
            "business_description": "desc",
            "revenue_cagr": 0.2,
            "profit_cagr": 0.15,
            "roe": 0.18,
        }

    def test_moat_pipeline_kwargs_defaults_missing_context_gracefully(self):
        kwargs = MoatAgent.pipeline_kwargs("TCS", {})
        assert kwargs == {"business_description": ""}

    def test_register_decorator_is_idempotent_on_reimport(self):
        # Re-registering under the same name should just overwrite, not raise/duplicate.
        before = AgentRegistry.available()
        AgentRegistry.register("moat")(MoatAgent)
        after = AgentRegistry.available()
        assert before == after
