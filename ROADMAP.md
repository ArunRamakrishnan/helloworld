# Investment Research Wizard — Roadmap

## Currently Built

### Agents (9)
- FundamentalAgent — ROE, D/E, FCF, Revenue CAGR (Graham/Buffett)
- ValuationAgent — P/E, P/B, EV/EBITDA, PEG, DCF with margin of safety
- MoatAgent — 7-dimension LLM moat scoring (Buffett)
- PhilipFisherAgent — R&D, management vision, 10x potential
- NewsAgent — NewsAPI + LLM sentiment, hype/fact separation
- SentimentAgent — Public RSS feeds (Moneycontrol, ET, LiveMint) + LLM
- UnicornDetectorAgent — Small cap, founder-led, emerging sector detection
- RiskAgent — Red flags, governance, debt traps
- Orchestrator — Master pipeline, LLM synthesis

### Universe Scan (Phase 3)
- UniverseScreenerAgent — Fast rule-based filter across NSE via yfinance
- QuarterlyEarningsAgent — Last 8 quarters, trend analysis, earnings quality score
- UniverseScanOrchestrator — Two-stage scan, Top 10 per category
- Async job runner with poll API (POST /scan/universe + GET /scan/universe/{job_id})

### API Endpoints (14)
- POST /research/{ticker} — Full 9-agent research
- POST /research/fisher/{ticker} — Fisher analysis only
- GET  /research/sentiment/{ticker} — Market sentiment
- POST /research/unicorn/{ticker} — Unicorn detection
- POST /report/daily — Morning report (user watchlist)
- POST /scan/universe — Start full NSE universe scan (async)
- GET  /scan/universe/{job_id} — Poll scan job
- GET  /scan/jobs — List recent scan jobs
- POST /orders/preview — Preview order
- POST /orders/place — Place paper/live order
- GET  /orders/paper-log — View paper trades
- POST /portfolio/suggest — Allocation bands
- GET  /categories — Stock categories
- GET  /disclaimer — SEBI disclaimer

### UI
- Streamlit dashboard — Single Stock, Morning Report, Universe Scanner, About

---

## TODO — Financial Data Sources

### TODO #1: Screener.in API Integration
**Priority:** High  
**Why:** More accurate and complete fundamental data for Indian stocks (10-year P&L history,
balance sheet trends, shareholding patterns, management commentary).

**What to do:**
1. Get Screener.in API access (contact: api@screener.in)
2. Create `src/data/screener_client.py`
3. Replace `DataCollectorAgent.fetch_financials_screener()` (currently a placeholder)
4. Add `SCREENER_API_KEY` to `.env.example` and `config.py`
5. Use Screener data in `UniverseScreenerAgent._fetch_stock_info()` as primary source,
   yfinance as fallback

**Key Screener endpoints to use:**
- `/api/company/?q={ticker}` — Search company
- `/api/company/{id}/` — Full fundamentals with 10-year history
- Includes: Revenue, PAT, EPS, Dividends, Promoter holding, Pledging, Peer comparison

---

### TODO #2: Trendlyne API Integration
**Priority:** High  
**Why:** Provides consensus analyst estimates, earnings beat/miss history, institutional
holding trends, and DVM (Durability, Valuation, Momentum) scores — all India-specific.

**What to do:**
1. Get Trendlyne API key (https://trendlyne.com/developer/)
2. Create `src/data/trendlyne_client.py`
3. Add consensus EPS estimates to `QuarterlyEarningsAgent` for earnings beat/miss detection
4. Add institutional holding data to `RiskAgent` (FII/DII buying = positive signal)
5. Add DVM score to `UniverseScreenerAgent` composite scoring
6. Add `TRENDLYNE_API_KEY` to `.env.example` and `config.py`

**Key Trendlyne data to use:**
- Analyst consensus targets (bull/base/bear)
- Earnings surprise history (beat/miss %)
- FII + DII holding changes (quarterly)
- Promoter buying/selling transactions
- DVM (Durability + Valuation + Momentum) composite score

---

### TODO #3: NSE Full Stock Universe (Beyond NIFTY 500)
**Priority:** Medium  
**Why:** Currently `UniverseScreenerAgent` screens NIFTY 500. True universe scan
should cover all ~1700 actively traded NSE stocks.

**What to do:**
1. Use NSE's CSV download: `https://www.nseindia.com/market-data/securities-available-for-trading`
2. Or use NSE bhav copy for full list of traded symbols
3. Update `NIFTY100_FALLBACK` to a fuller static list
4. Add BSE support (append `.BO` suffix for yfinance)

---

### TODO #4: Real-Time Price Feed
**Priority:** Medium  
**Why:** yfinance has 15-min delay. For intraday signals, need WebSocket feed.

**What to do:**
1. Add Zerodha KiteTicker WebSocket for real-time NSE prices
2. Store in Redis with TTL = 1 minute
3. Use in `UniverseScreenerAgent` for current_price instead of yfinance

---

### TODO #5: Kafka + Airflow for Production Scale
**Priority:** Low (Phase 4)  
**Why:** For running daily automated scans at 6 AM without manual trigger.

**What to do:**
1. Create Kafka topics: `stock.research.requested`, `stock.research.completed`
2. Airflow DAG: runs at 6:00 AM IST → triggers universe scan → publishes to Kafka
3. Consumer service: reads from Kafka, stores results in PostgreSQL
4. API reads pre-computed results instead of running on-demand

---

### TODO #6: Social Sentiment (Twitter / Reddit)
**Priority:** Low  
**Why:** Retail sentiment from social media can be a contrarian signal.

**What to do:**
1. Twitter/X API v2 for stock mentions ($RELIANCE, #NSE)
2. Reddit r/IndiaInvestments scraper
3. Integrate into `SentimentAgent` as additional signal source
4. Mark social signals as "unverified" in output

---

## Tech Debt

- `src/data/repository.py` — DB layer exists but not wired to agents (no persistence yet)
- `src/data/models.py` — SQLAlchemy models defined but migrations not run in prod
- `AuditAgent` — Prompt versioning exists but not exposed via API
- Broker live mode — Zerodha/Upstox/Angel/Dhan wrappers are stubs; need real auth flows
