"""Central configuration — reads from environment variables."""
import os
from dataclasses import dataclass, field
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class BrokerConfig:
    zerodha_api_key: Optional[str] = field(default_factory=lambda: os.getenv("ZERODHA_API_KEY"))
    zerodha_api_secret: Optional[str] = field(default_factory=lambda: os.getenv("ZERODHA_API_SECRET"))
    upstox_api_key: Optional[str] = field(default_factory=lambda: os.getenv("UPSTOX_API_KEY"))
    upstox_api_secret: Optional[str] = field(default_factory=lambda: os.getenv("UPSTOX_API_SECRET"))
    angel_api_key: Optional[str] = field(default_factory=lambda: os.getenv("ANGEL_API_KEY"))
    angel_client_id: Optional[str] = field(default_factory=lambda: os.getenv("ANGEL_CLIENT_ID"))
    dhan_client_id: Optional[str] = field(default_factory=lambda: os.getenv("DHAN_CLIENT_ID"))
    dhan_access_token: Optional[str] = field(default_factory=lambda: os.getenv("DHAN_ACCESS_TOKEN"))


@dataclass
class DatabaseConfig:
    postgres_url: str = field(
        default_factory=lambda: os.getenv(
            "POSTGRES_URL", "postgresql://user:password@localhost:5432/investment_agent"
        )
    )
    chroma_host: str = field(default_factory=lambda: os.getenv("CHROMA_HOST", "localhost"))
    chroma_port: int = field(default_factory=lambda: int(os.getenv("CHROMA_PORT", "8000")))
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379/0"))


@dataclass
class LLMConfig:
    anthropic_api_key: Optional[str] = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY"))
    model: str = "claude-opus-4-8"
    max_tokens: int = 8192


@dataclass
class AppConfig:
    paper_trading: bool = field(
        default_factory=lambda: os.getenv("PAPER_TRADING", "true").lower() == "true"
    )
    news_api_key: Optional[str] = field(default_factory=lambda: os.getenv("NEWS_API_KEY"))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    broker: BrokerConfig = field(default_factory=BrokerConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)


def get_config() -> AppConfig:
    return AppConfig()
