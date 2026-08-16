"""Unit tests for the layered config system (config/default.yaml + env overrides)."""
import pytest

from src.utils.config import get_config, reload_config
from src.utils.config_loader import _deep_merge, load_yaml_config


@pytest.fixture(autouse=True)
def _restore_real_config():
    """Ensures the process-wide config singleton is back to real values after each test,
    even if a test monkeypatches env vars that get_config()/reload_config() read."""
    yield
    reload_config()


class TestDeepMerge:
    def test_override_replaces_scalar(self):
        base = {"a": 1, "b": {"c": 2}}
        override = {"a": 9}
        assert _deep_merge(base, override) == {"a": 9, "b": {"c": 2}}

    def test_override_merges_nested_dict(self):
        base = {"scoring": {"risk": {"x": 1, "y": 2}}}
        override = {"scoring": {"risk": {"y": 99}}}
        merged = _deep_merge(base, override)
        assert merged == {"scoring": {"risk": {"x": 1, "y": 99}}}

    def test_override_replaces_list_entirely(self):
        base = {"pipeline": {"enabled_agents": ["moat", "news"]}}
        override = {"pipeline": {"enabled_agents": ["moat"]}}
        merged = _deep_merge(base, override)
        assert merged["pipeline"]["enabled_agents"] == ["moat"]

    def test_base_not_mutated(self):
        base = {"a": {"b": 1}}
        _deep_merge(base, {"a": {"b": 2}})
        assert base == {"a": {"b": 1}}


class TestLoadYamlConfig:
    def test_default_only_when_env_file_missing(self, tmp_path):
        (tmp_path / "default.yaml").write_text("app:\n  disclaimer: base\n")
        data = load_yaml_config("nonexistent_env", config_dir=tmp_path)
        assert data["app"]["disclaimer"] == "base"

    def test_env_file_overrides_default(self, tmp_path):
        (tmp_path / "default.yaml").write_text("broker:\n  active_broker: zerodha\n")
        (tmp_path / "production.yaml").write_text("broker:\n  active_broker: upstox\n")
        data = load_yaml_config("production", config_dir=tmp_path)
        assert data["broker"]["active_broker"] == "upstox"

    def test_env_var_interpolation(self, tmp_path, monkeypatch):
        monkeypatch.setenv("TEST_INTERP_VALUE", "hello")
        (tmp_path / "default.yaml").write_text("app:\n  disclaimer: '${TEST_INTERP_VALUE}-world'\n")
        data = load_yaml_config("development", config_dir=tmp_path)
        assert data["app"]["disclaimer"] == "hello-world"


class TestAppConfigDefaults:
    """Spot-checks that config/default.yaml values match the pre-refactor hardcoded
    constants, so retrofitted agents behave identically to before."""

    def test_disclaimer_mentions_sebi(self):
        assert "SEBI" in get_config().disclaimer

    def test_six_categories(self):
        cfg = get_config()
        assert len(cfg.categories) == 6
        assert {c.id for c in cfg.categories} == {
            "long_term_compounder", "undervalued_value", "turnaround",
            "dividend_income", "momentum_risky", "avoid_watchlist",
        }

    def test_default_pipeline_order(self):
        assert get_config().pipeline.enabled_agents == ["moat", "news", "sentiment", "fisher", "unicorn"]

    def test_default_active_broker(self):
        assert get_config().broker.active_broker == "zerodha"

    def test_fundamental_roe_tiers_match_old_thresholds(self):
        tiers = get_config().scoring.fundamental.roe_tiers
        assert tiers[0] == (0.30, 10.0)
        assert tiers[1] == (0.20, 8.0)
        assert tiers[2] == (0.15, 6.0)
        assert tiers[3] == (0.10, 4.0)

    def test_valuation_weights_sum_to_one(self):
        weights = get_config().scoring.valuation.weights
        assert sum(weights.values()) == pytest.approx(1.0)

    def test_moat_weights_sum_to_one(self):
        weights = get_config().scoring.moat.weights
        assert sum(weights.values()) == pytest.approx(1.0)

    def test_portfolio_max_single_stock_pct_matches_old_constants(self):
        rules = get_config().scoring.portfolio.max_single_stock_pct
        assert rules == {"conservative": 5.0, "moderate": 8.0, "aggressive": 12.0}


class TestConfigPrecedence:
    def test_active_broker_env_var_overrides_yaml(self, monkeypatch):
        monkeypatch.setenv("ACTIVE_BROKER", "upstox")
        cfg = reload_config()
        assert cfg.broker.active_broker == "upstox"

    def test_paper_trading_env_var_parsed_as_bool(self, monkeypatch):
        monkeypatch.setenv("PAPER_TRADING", "false")
        cfg = reload_config()
        assert cfg.paper_trading is False

    def test_get_config_is_cached_singleton(self):
        assert get_config() is get_config()
