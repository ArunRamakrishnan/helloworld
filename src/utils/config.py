"""
Central configuration.

Business rules (scoring thresholds/weights, the enrichment-agent pipeline, broker
selection, disclaimer/category text) live in config/default.yaml (+ optional
config/<APP_ENV>.yaml override) — see docs/configuration.md.

Secrets and deployment knobs (API keys, DB URLs, PAPER_TRADING, LOG_LEVEL, APP_ENV,
ACTIVE_BROKER) are read from environment variables / `.env` and always take
precedence — they are never stored in the YAML files.
"""
import os
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict

from src.utils.config_loader import load_yaml_config

load_dotenv()

Tier = Tuple[float, float]

DEFAULT_POSTGRES_URL = "postgresql://user:password@localhost:5432/investment_agent"


class BrokerConfig(BaseModel):
    active_broker: str = "zerodha"
    zerodha_api_key: Optional[str] = None
    zerodha_api_secret: Optional[str] = None
    upstox_api_key: Optional[str] = None
    upstox_api_secret: Optional[str] = None
    angel_api_key: Optional[str] = None
    angel_client_id: Optional[str] = None
    dhan_client_id: Optional[str] = None
    dhan_access_token: Optional[str] = None


class DatabaseConfig(BaseModel):
    postgres_url: str = DEFAULT_POSTGRES_URL
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    redis_url: str = "redis://localhost:6379/0"


class LLMConfig(BaseModel):
    anthropic_api_key: Optional[str] = None
    model: str = "claude-opus-4-8"
    max_tokens: int = 8192
    max_tokens_per_agent: Dict[str, int] = {}

    def max_tokens_for(self, agent: str) -> int:
        return self.max_tokens_per_agent.get(agent, self.max_tokens)


class CategoryInfo(BaseModel):
    id: str
    name: str
    description: str


# ------------------------------------------------------------------
# Scoring config — one sub-model per agent, defaults sourced from
# config/default.yaml. See src/utils/scoring.py for how tiers are evaluated.
# ------------------------------------------------------------------

class FundamentalScoringConfig(BaseModel):
    weights: Dict[str, float]
    roe_tiers: List[Tier]
    roe_no_match: float
    roe_if_none: float
    debt_equity_tiers: List[Tier]
    debt_equity_no_match: float
    debt_equity_if_none: float
    revenue_cagr_tiers: List[Tier]
    revenue_cagr_no_match: float
    revenue_cagr_if_none: float
    fcf_ratio_tiers: List[Tier]
    fcf_ratio_no_match: float


class DcfDefaults(BaseModel):
    growth_rate_yr1_5: float
    growth_rate_yr6_10: float
    terminal_growth_rate: float
    discount_rate: float
    margin_of_safety: float


class ValuationScoringConfig(BaseModel):
    weights: Dict[str, float]
    pe_tiers: List[Tier]
    pe_no_match: float
    pe_if_none: float
    pb_tiers: List[Tier]
    pb_no_match: float
    pb_if_none: float
    peg_tiers: List[Tier]
    peg_no_match: float
    peg_if_none: float
    margin_of_safety_tiers: List[Tier]
    margin_of_safety_no_match: float
    margin_of_safety_if_none: float
    dcf_defaults: DcfDefaults


class RiskScoringConfig(BaseModel):
    high_debt_de_threshold: float
    overvalued_pe_threshold: float
    high_promoter_pledge_pct: float
    low_promoter_holding_pct: float
    severe_flags: List[str]
    severe_flag_points: float
    normal_flag_points: float
    debt_penalty_tiers: List[Tier]
    risk_label_low_max: float
    risk_label_moderate_max: float
    red_flag_descriptions: Dict[str, str]


class MoatScoringConfig(BaseModel):
    weights: Dict[str, float]
    fallback_score: float = 5.0


class FisherScoringConfig(BaseModel):
    weights: Dict[str, float]
    fallback_score: float = 5.0


class UnicornScoringConfig(BaseModel):
    weights: Dict[str, float]
    small_cap_max_cr: float
    mid_cap_max_cr: float
    ten_x_candidate_threshold: float
    quant_score_boost_cap: float


class PortfolioScoringConfig(BaseModel):
    max_single_stock_pct: Dict[str, float]
    max_sector_pct: Dict[str, float]
    emergency_fund_min_months: int
    eligible_risk_score_max: Dict[str, float]
    non_strong_weight_factor: float
    composite_weights: Dict[str, float]


class SynthesisScoringConfig(BaseModel):
    growth_tiers: List[Tier]
    growth_no_match: float
    avoid_risk_threshold: float
    avoid_confidence: float
    strong_unicorn_score_threshold: float
    strong_unicorn_risk_max: float
    strong_unicorn_confidence: float
    strong_core_financial_min: float
    strong_core_valuation_min: float
    strong_core_moat_min: float
    strong_core_risk_max: float
    strong_core_confidence: float
    strong_fisher_score_min: float
    strong_fisher_unicorn_min: float
    strong_fisher_confidence: float
    watch_confidence: float


class ScoringConfig(BaseModel):
    fundamental: FundamentalScoringConfig
    valuation: ValuationScoringConfig
    risk: RiskScoringConfig
    moat: MoatScoringConfig
    fisher: FisherScoringConfig
    unicorn: UnicornScoringConfig
    portfolio: PortfolioScoringConfig
    synthesis: SynthesisScoringConfig


class PipelineConfig(BaseModel):
    enabled_agents: List[str] = []


class AppConfig(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    paper_trading: bool = True
    news_api_key: Optional[str] = None
    log_level: str = "INFO"
    disclaimer: str
    categories: List[CategoryInfo]
    broker: BrokerConfig
    database: DatabaseConfig
    llm: LLMConfig
    scoring: ScoringConfig
    pipeline: PipelineConfig


def _build_app_config() -> AppConfig:
    env = os.getenv("APP_ENV", "development")
    yaml_data = load_yaml_config(env)

    app_meta = yaml_data.get("app", {})
    broker_yaml = yaml_data.get("broker", {})
    llm_yaml = yaml_data.get("llm", {})
    scoring_yaml = yaml_data.get("scoring", {})
    pipeline_yaml = yaml_data.get("pipeline", {})

    broker = BrokerConfig(
        active_broker=os.getenv("ACTIVE_BROKER", broker_yaml.get("active_broker", "zerodha")),
        zerodha_api_key=os.getenv("ZERODHA_API_KEY"),
        zerodha_api_secret=os.getenv("ZERODHA_API_SECRET"),
        upstox_api_key=os.getenv("UPSTOX_API_KEY"),
        upstox_api_secret=os.getenv("UPSTOX_API_SECRET"),
        angel_api_key=os.getenv("ANGEL_API_KEY"),
        angel_client_id=os.getenv("ANGEL_CLIENT_ID"),
        dhan_client_id=os.getenv("DHAN_CLIENT_ID"),
        dhan_access_token=os.getenv("DHAN_ACCESS_TOKEN"),
    )

    database = DatabaseConfig(
        postgres_url=os.getenv("POSTGRES_URL", DEFAULT_POSTGRES_URL),
        chroma_host=os.getenv("CHROMA_HOST", "localhost"),
        chroma_port=int(os.getenv("CHROMA_PORT", "8000")),
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
    )

    llm = LLMConfig(
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
        model=llm_yaml.get("model", "claude-opus-4-8"),
        max_tokens=llm_yaml.get("max_tokens", 8192),
        max_tokens_per_agent=llm_yaml.get("max_tokens_per_agent", {}),
    )

    return AppConfig(
        paper_trading=os.getenv("PAPER_TRADING", "true").lower() == "true",
        news_api_key=os.getenv("NEWS_API_KEY"),
        log_level=os.getenv("LOG_LEVEL", "INFO"),
        disclaimer=app_meta.get("disclaimer", "").strip(),
        categories=app_meta.get("categories", []),
        broker=broker,
        database=database,
        llm=llm,
        scoring=ScoringConfig(**scoring_yaml),
        pipeline=PipelineConfig(**pipeline_yaml),
    )


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    return _build_app_config()


def reload_config() -> AppConfig:
    """Clears the cached config and rebuilds it from current env vars + YAML files.

    Use after mutating os.environ in tests, or after editing config/*.yaml at runtime.
    """
    get_config.cache_clear()
    return get_config()
