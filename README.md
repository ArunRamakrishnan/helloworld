# Indian Investment Research Wizard Agent

A safe, explainable AI-powered investment research platform for NSE/BSE Indian equities.

> **Disclaimer:** This is an educational research tool. It does not provide financial advice. Always consult a SEBI-registered investment adviser before investing.

## What This Does

- Screens Indian stocks across NSE and BSE using proven value-investing frameworks
- Produces detailed research reports with confidence scores, risk scores, and evidence
- Classifies stocks into: Long-term Compounders, Undervalued Value, Turnaround, Dividend, Momentum (Risky), Avoid/Watchlist
- Defaults to **paper trading** — real orders require explicit user confirmation
- Never promises returns or guarantees outcomes

## Architecture

```
investment-agent/
├── src/agents/          # 9 specialized AI agents
├── src/api/             # FastAPI backend
├── src/brokers/         # Zerodha, Upstox, DhanHQ, Angel One connectors
├── src/data/            # PostgreSQL models and repository layer
├── src/utils/           # Logging, config, validators
├── tests/               # 100% business use case coverage
├── prompts/             # All prompts versioned with date
└── docs/                # Architecture, compliance, changelog
```

## Agent Modules

| Agent | Purpose |
|-------|---------|
| Data Collector | Fetches stock universe, prices, financials, filings, news |
| Fundamental Analysis | Revenue/profit CAGR, ROE, ROCE, debt, FCF |
| Valuation | PE, PB, EV/EBITDA, PEG, DCF with margin of safety |
| Moat & Business Quality | Brand, switching cost, network effect, management |
| Risk | Red flags: debt, cash flow, promoter pledge, governance |
| News & Sentiment | Verified news summary, separates fact from hype |
| Portfolio Construction | Allocation bands based on user risk profile |
| Broker Execution | Paper-trading default; real orders need confirmation |
| Audit & Prompt Version | Tracks every change, prompt, commit, and test result |

## Investment Frameworks

Inspired by: Benjamin Graham, Warren Buffett, Charlie Munger, Peter Lynch, Philip Fisher, Howard Marks, and modern factor investing.

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/arunramakrishnan/helloworld.git
cd helloworld
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys

# 3. Run in paper-trading mode (default)
uvicorn src.api.main:app --reload

# 4. Run tests
pytest tests/ -v
```

## Data Sources (Legal Only)

- NSE/BSE public data and exchange filings
- Company annual reports and investor presentations
- Broker APIs: Zerodha Kite Connect, Upstox, Angel One SmartAPI, DhanHQ, Fyers, ICICI Breeze
- News APIs
- SEBI announcements
- RBI/macroeconomic data
- Mutual fund/shareholding data

## Safety Rules

- No guaranteed return claims
- No intraday/options/F&O advice for beginners
- No real trades without explicit user confirmation
- No scraping of restricted data
- Every recommendation includes uncertainty and risk disclosure

## Tech Stack

- **Backend:** Python 3.11+, FastAPI
- **LLM:** Anthropic Claude (claude-opus-4-8)
- **Database:** PostgreSQL (structured), ChromaDB (embeddings)
- **Data:** Pandas, NumPy
- **Testing:** Pytest
- **CI:** GitHub Actions
- **UI:** Streamlit (Phase 1), React (Phase 2)
- **Infrastructure:** Docker, docker-compose

## Contributing

Every code change must:
1. Update `docs/CHANGELOG.md`
2. Save prompt version to `prompts/prompt_versions/`
3. Pass all unit and integration tests
4. Include git commit with descriptive message

## License

Private repository — not for public distribution.
