# Third-party integrations

Every external integration is optional and fails soft — if its credentials aren't
configured, the relevant agent falls back to rule-based/keyword logic or returns an
empty result rather than erroring. See [`docs/configuration.md`](configuration.md)
for how config/secrets are layered.

## Summary

| # | Service | Type | Purpose | Auth required? |
|---|---------|------|---------|-----------------|
| 1 | Anthropic Claude API | LLM | Moat, Fisher, Unicorn, News, Sentiment analysis + final synthesis | Yes — `ANTHROPIC_API_KEY` |
| 2 | NSE India (public endpoint) | Market data | Stock universe / index constituents | No |
| 3 | Yahoo Finance (`yfinance`) | Market data | Historical daily OHLCV prices | No |
| 4 | NewsAPI (newsapi.org) | News | Recent news articles per ticker | Yes — `NEWS_API_KEY` |
| 5 | Moneycontrol RSS | News/Sentiment | Headlines for sentiment scoring | No |
| 6 | Economic Times RSS | News/Sentiment | Headlines for sentiment scoring | No |
| 7 | LiveMint RSS | News/Sentiment | Headlines for sentiment scoring | No |
| 8 | Zerodha Kite Connect | Broker | Place/cancel orders, holdings, positions | Yes — `ZERODHA_API_KEY` / `ZERODHA_API_SECRET` |
| 9 | Upstox API v2 | Broker | Place/cancel orders | Yes — `UPSTOX_API_KEY` / `UPSTOX_API_SECRET` |
| 10 | Angel One SmartAPI | Broker | Place/cancel orders | Yes — `ANGEL_API_KEY` / `ANGEL_CLIENT_ID` |
| 11 | DhanHQ | Broker | Place/cancel orders | Yes — `DHAN_CLIENT_ID` / `DHAN_ACCESS_TOKEN` |

## LLM

### 1. Anthropic Claude API
- **Used by:** `src/agents/orchestrator.py` (final synthesis), `moat_agent.py`,
  `fisher_agent.py`, `news_agent.py`, `sentiment_agent.py`, `unicorn_detector.py`
- **Client:** `anthropic` Python SDK
- **Config:** `ANTHROPIC_API_KEY` env var; model/max_tokens tunable in
  `config/default.yaml` under `llm.model` / `llm.max_tokens_per_agent`
- **Fallback if not configured:** each agent returns a neutral/rule-based result
  (e.g. moat/fisher/unicorn dimensions default to a fallback score, synthesis uses
  `Orchestrator._rule_based_synthesis`)

## Market data

### 2. NSE India
- **Used by:** `src/agents/data_collector.py::fetch_nse_stock_list`
- **Endpoint:** `https://www.nseindia.com/api/equity-stockIndices` (public, no key)
- **Purpose:** NIFTY 500 stock universe (ticker, name, sector, exchange)
- **Fallback:** returns an empty list on failure; universe scan agents have a
  hardcoded `NIFTY100_FALLBACK` / `UNICORN_UNIVERSE` symbol list to use instead

### 3. Yahoo Finance (`yfinance`)
- **Used by:** `data_collector.py::fetch_historical_prices`, `universe_screener.py`,
  `unicorn_hunter.py`, `quarterly_earnings.py`
- **Purpose:** daily OHLCV price history (ticker suffixed `.NS` for NSE)
- **Auth:** none — public library, no API key
- **Fallback:** returns an empty list/dict if the package isn't installed or the
  fetch fails; retried with backoff on HTTP 429 (rate limit)

## News

### 4. NewsAPI (newsapi.org)
- **Used by:** `data_collector.py::fetch_news`
- **Config:** `NEWS_API_KEY` env var
- **Purpose:** recent news articles per ticker, feeding `NewsAgent` and `SentimentAgent`
- **Fallback:** skipped entirely (empty list) if no key is set

### 5–7. RSS feeds (Moneycontrol, Economic Times, LiveMint)
- **Used by:** `sentiment_agent.py::fetch_rss_headlines`
- **Auth:** none — public RSS, no API key
- **Purpose:** headlines filtered for ticker mentions, feeding sentiment analysis
- **Fallback:** a feed that's unreachable is silently skipped; overall sentiment
  falls back to keyword-based scoring if no headlines are found or the LLM is
  unavailable

## Brokers

All four share a common interface (`src/brokers/base.py::BrokerConnector`) and are
selected at runtime by `BrokerFactory` via `config.broker.active_broker`
(`ACTIVE_BROKER` env var, default `zerodha`) — see
[`docs/configuration.md`](configuration.md#adding-a-new-broker--no-brokeragent-edit).
**Paper trading is on by default** (`PAPER_TRADING=true`); no broker is called at all
unless it's turned off.

### 8. Zerodha Kite Connect
- **SDK:** `kiteconnect` (`pip install kiteconnect`)
- **Config:** `ZERODHA_API_KEY`, `ZERODHA_API_SECRET`
- **Supports:** place/cancel orders, holdings, positions

### 9. Upstox API v2
- **SDK:** `upstox-python-sdk`
- **Config:** `UPSTOX_API_KEY`, `UPSTOX_API_SECRET`
- **Supports:** place/cancel orders

### 10. Angel One SmartAPI
- **SDK:** `smartapi-python`
- **Config:** `ANGEL_API_KEY`, `ANGEL_CLIENT_ID`
- **Supports:** place/cancel orders

### 11. DhanHQ
- **SDK:** `dhanhq`
- **Config:** `DHAN_CLIENT_ID`, `DHAN_ACCESS_TOKEN`
- **Supports:** place/cancel orders

## Not yet integrated (mentioned in README as future/optional data sources)

Fyers, ICICI Breeze, RBI/macroeconomic data, SEBI announcements, and mutual
fund/shareholding data are listed in the README's "Data Sources" section as intended
sources but have no connector code yet.
