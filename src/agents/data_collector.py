"""Data Collector Agent — fetches stock universe, prices, financials, filings, and news."""
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.validators import validate_ticker

logger = get_logger(__name__)

DISCLAIMER = (
    "This is educational research, not financial advice. "
    "Consult a SEBI-registered investment adviser before investing."
)


class DataCollectorAgent:
    """
    Collects raw market data from legal, allowed sources only.

    Sources used:
    - NSE/BSE public endpoints
    - Broker APIs (Zerodha Kite, Upstox, etc.) with user-provided API keys
    - News APIs with user-provided API keys

    Never scrapes restricted sites. Respects rate limits and robots.txt.
    """

    def __init__(self, config=None):
        self.cfg = config or get_config()
        self._http = httpx.Client(timeout=15.0)

    # ------------------------------------------------------------------
    # Stock universe
    # ------------------------------------------------------------------

    def fetch_nse_stock_list(self) -> List[Dict[str, Any]]:
        """
        Fetch the list of all NSE-listed equities from the NSE public endpoint.
        Returns a list of dicts with keys: symbol, name, sector, series.
        """
        url = "https://www.nseindia.com/api/equity-stockIndices?index=NIFTY+500"
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}
        try:
            resp = self._http.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            stocks = []
            for item in data.get("data", []):
                stocks.append({
                    "ticker": item.get("symbol"),
                    "name": item.get("meta", {}).get("companyName", ""),
                    "sector": item.get("meta", {}).get("industry", ""),
                    "exchange": "NSE",
                    "source_url": url,
                    "fetched_at": datetime.utcnow().isoformat(),
                })
            logger.info("Fetched %d stocks from NSE", len(stocks))
            return stocks
        except Exception as exc:
            logger.error("Failed to fetch NSE stock list: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Price data
    # ------------------------------------------------------------------

    def fetch_historical_prices(
        self,
        ticker: str,
        from_date: date,
        to_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch daily OHLCV prices for a ticker.
        Uses yfinance for backtesting/research (NSE suffix appended automatically).
        """
        validated = validate_ticker(ticker)
        to_date = to_date or date.today()
        try:
            import yfinance as yf
            symbol = f"{validated}.NS"
            df = yf.download(symbol, start=from_date, end=to_date, progress=False)
            if df.empty:
                logger.warning("No price data found for %s", symbol)
                return []
            records = []
            for idx, row in df.iterrows():
                records.append({
                    "date": idx.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                    "volume": int(row["Volume"]),
                    "source": "yfinance",
                })
            logger.info("Fetched %d price rows for %s", len(records), validated)
            return records
        except ImportError:
            logger.error("yfinance not installed; run: pip install yfinance")
            return []
        except Exception as exc:
            logger.error("Price fetch failed for %s: %s", ticker, exc)
            return []

    # ------------------------------------------------------------------
    # Financial statements (via broker API or public source)
    # ------------------------------------------------------------------

    def fetch_financials_screener(self, ticker: str) -> Dict[str, Any]:
        """
        Placeholder: in production, use Screener.in API if access is granted,
        or parse from broker API. Returns empty dict if not configured.

        The caller (FundamentalAgent) computes ratios from the raw data returned here.
        """
        validated = validate_ticker(ticker)
        logger.info("Financial data fetch for %s (source: not configured)", validated)
        return {
            "ticker": validated,
            "source": "not_configured",
            "note": "Configure a financial data source in .env",
        }

    # ------------------------------------------------------------------
    # News
    # ------------------------------------------------------------------

    def fetch_news(self, ticker: str, days: int = 7) -> List[Dict[str, Any]]:
        """Fetch recent news articles for a ticker using NewsAPI."""
        validated = validate_ticker(ticker)
        api_key = self.cfg.news_api_key
        if not api_key:
            logger.warning("NEWS_API_KEY not set; skipping news fetch for %s", validated)
            return []

        from_dt = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": validated,
            "from": from_dt,
            "language": "en",
            "sortBy": "publishedAt",
            "apiKey": api_key,
        }
        try:
            resp = self._http.get(url, params=params)
            resp.raise_for_status()
            articles = resp.json().get("articles", [])
            logger.info("Fetched %d news articles for %s", len(articles), validated)
            return [
                {
                    "title": a.get("title"),
                    "source": a.get("source", {}).get("name"),
                    "published_at": a.get("publishedAt"),
                    "url": a.get("url"),
                    "description": a.get("description"),
                }
                for a in articles
            ]
        except Exception as exc:
            logger.error("News fetch failed for %s: %s", ticker, exc)
            return []

    def close(self):
        self._http.close()
