# Architecture — Indian Investment Research Wizard Agent

## System Overview

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                        │
│              (Streamlit / React Dashboard)               │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP/WebSocket
┌────────────────────────▼────────────────────────────────┐
│                   FastAPI Backend                        │
│                   src/api/main.py                        │
└──┬────────┬────────┬────────┬────────┬──────────────────┘
   │        │        │        │        │
   ▼        ▼        ▼        ▼        ▼
 Data    Fundmtl  Valutn   Risk    Portfolio
Coll.    Agent    Agent   Agent    Agent
   │        │        │        │        │
   └────────┴────────┴────────┴────────┘
                    │
         ┌──────────▼──────────┐
         │   Claude LLM Layer  │
         │  (claude-opus-4-8)  │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │    Broker Agent     │
         │  (Paper / Live)     │
         └──────────┬──────────┘
                    │
    ┌───────────────▼───────────────┐
    │          Broker APIs           │
    │  Zerodha / Upstox / Angel One  │
    └───────────────────────────────┘
```

## Data Flow

1. **Ingest** — Data Collector fetches stock universe, prices, financials from NSE/BSE and broker APIs
2. **Analyze** — Fundamental, Valuation, Moat, Risk, News agents process raw data in parallel
3. **Synthesize** — Claude LLM orchestrates agent outputs into a unified research report
4. **Score** — Each stock receives Financial Strength, Growth, Valuation, Moat, Risk scores out of 10
5. **Classify** — Stocks are placed into one of 6 categories
6. **Act** — Portfolio agent suggests allocation; Broker agent executes (paper-trade by default)

## Database Schema

### PostgreSQL Tables
- `stocks` — master list (ticker, name, sector, exchange)
- `prices` — daily OHLCV data
- `financials` — quarterly/annual P&L, balance sheet, cash flow
- `ratios` — computed PE, PB, ROE, ROCE, CAGR
- `research_reports` — generated reports with scores
- `orders` — paper and live order log
- `user_profiles` — risk appetite, horizon, holdings

### ChromaDB Collections
- `filings_embeddings` — annual report / DRHP chunks
- `news_embeddings` — news article embeddings

## Agent Responsibilities

| Agent | Input | Output |
|-------|-------|--------|
| DataCollector | API keys, tickers | Raw OHLCV, financials, filings |
| FundamentalAgent | Raw financials | ROE, ROCE, CAGR, FCF, debt scores |
| ValuationAgent | Prices + financials | PE, PB, EV/EBITDA, DCF, margin of safety |
| MoatAgent | Business description + LLM | Moat score /10 with evidence |
| RiskAgent | All signals | Red flag list, risk score /10 |
| NewsAgent | News API results | Sentiment summary, fact/hype separation |
| PortfolioAgent | Risk profile + reports | Allocation bands (%) |
| BrokerAgent | Order intent | Paper-trade log or live order confirmation |
| AuditAgent | Code changes, test results | Versioned prompt/changelog entry |

## Security and Compliance

- API keys stored in `.env` (never committed)
- Real broker orders require explicit user confirmation + audit log
- No data scraped from sources with restrictive ToS
- SEBI disclaimer on every output
- Rate limiting on all external API calls
