# Running the app — step by step

Two ways to run this locally: **quick path** (just the API, in-memory/no external
services, good for trying it out) and **full path** (API + Postgres + Chroma + Redis
via Docker, plus the Streamlit UI).

## Quick path — API only

```bash
# 1. Clone (skip if you already have the repo)
git clone https://github.com/ArunRamakrishnan/helloworld.git
cd helloworld

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your local env file
cp .env.example .env
# Open .env and fill in at least ANTHROPIC_API_KEY if you want real LLM-backed
# analysis (moat/fisher/unicorn/news/sentiment/synthesis). Leaving it blank still
# works — those agents fall back to rule-based/neutral scoring.

# 5. Run the API (paper trading is on by default — no real orders/money)
uvicorn src.api.main:app --reload

# 6. In another terminal, confirm it's up
curl http://127.0.0.1:8000/health
```

Open **http://127.0.0.1:8000/docs** for interactive Swagger docs to try every
endpoint (research, portfolio, orders, universe scan, etc.) from the browser.

## Full path — with Postgres / Chroma / Redis (Docker)

```bash
# 1-4. Same as above (clone, venv, install, .env) — Docker Compose still reads .env

# 5. Start everything (Postgres, Chroma, Redis, API) with Docker
docker compose up --build

# 6. Confirm it's up (API is on port 8080 in this mode, see docker-compose.yml)
curl http://127.0.0.1:8080/health
```

## Streamlit dashboard (optional, either path)

```bash
# In a separate terminal, with the venv activated and the API already running
streamlit run streamlit_app.py
```

Opens at **http://localhost:8501**.

## Run the test suite

```bash
pytest tests/ -v
```

## Try a research request from the CLI

```bash
curl -X POST http://127.0.0.1:8000/api/v1/research/RELIANCE \
  -H "Content-Type: application/json" \
  -d '{
    "ticker": "RELIANCE",
    "current_price": 2850.5,
    "market_cap_cr": 1930000,
    "business_description": "Reliance Industries is a diversified conglomerate in energy, retail, and telecom.",
    "eps": 97.0,
    "book_value_per_share": 1100.0,
    "debt_cr": 300000,
    "cash_cr": 150000,
    "ebitda_cr": 180000,
    "fcf_cr": 60000,
    "shares_outstanding_cr": 676,
    "statements": []
  }'
```

## Try the IPO Watch / IPO Unicorn Hunt from the CLI

```bash
# SEBI/NSE/BSE IPO details — current, upcoming, and recently-listed
curl http://127.0.0.1:8000/api/v1/ipo

# Start an async IPO Unicorn Hunt (returns a job_id to poll)
curl -X POST http://127.0.0.1:8000/api/v1/ipo/unicorn-hunt \
  -H "Content-Type: application/json" \
  -d '{"lookback_months": 12, "top_n": 20}'

# Poll for results
curl http://127.0.0.1:8000/api/v1/ipo/unicorn-hunt/<job_id>
```

## Notes

- **Paper trading is on by default** (`PAPER_TRADING=true` in `.env`) — no real
  broker orders are placed unless you explicitly set it to `false` and configure
  broker credentials.
- Scoring rules, which agents run, and broker selection are configurable without
  code changes — see [`docs/configuration.md`](docs/configuration.md).
- To stop: `Ctrl+C` the `uvicorn`/`streamlit` process, or `docker compose down` for
  the full path.
