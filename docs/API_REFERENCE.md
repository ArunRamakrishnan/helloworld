# API Reference — Indian Investment Research Wizard

**Base URL:** `http://localhost:8080/api/v1`  
**Interactive Docs (Swagger):** `http://localhost:8080/docs`  
**Health Check:** `GET http://localhost:8080/health`

> ⚠️ **Disclaimer:** All endpoints return educational research only — not financial advice.  
> Consult a SEBI-registered investment adviser before investing.

---

## Table of Contents

| # | Endpoint | Method | Purpose |
|---|----------|--------|---------|
| 1 | `/research/{ticker}` | POST | Full 9-agent research report on a stock |
| 2 | `/research/fisher/{ticker}` | POST | Philip Fisher analysis only |
| 3 | `/research/sentiment/{ticker}` | GET | Market sentiment from RSS + LLM |
| 4 | `/research/unicorn/{ticker}` | POST | Unicorn / small cap potential detection |
| 5 | `/report/daily` | POST | Morning report — Top 3 per category across a watchlist |
| 6 | `/orders/preview` | POST | Preview a BUY/SELL order (no execution) |
| 7 | `/orders/place` | POST | Place a paper or live order |
| 8 | `/orders/paper-log` | GET | View all paper trading orders placed |
| 9 | `/portfolio/suggest` | POST | Suggest allocation bands for a user profile |
| 10 | `/categories` | GET | List the 6 stock classification categories |
| 11 | `/disclaimer` | GET | Fetch the SEBI disclaimer text |

---

## 1. Full Research Report

### `POST /api/v1/research/{ticker}`

Runs all 9 agents in sequence and produces a complete research report for a single stock. This is the **main endpoint** — use this for end-to-end analysis.

**Agents executed:**
1. FundamentalAgent — ROE, D/E, revenue CAGR, FCF
2. ValuationAgent — P/E, P/B, EV/EBITDA, PEG, DCF with margin of safety
3. MoatAgent (LLM) — 7 moat dimensions (brand, switching cost, network effect, etc.)
4. PhilipFisherAgent (LLM) — R&D, management vision, 10x potential
5. NewsAgent (LLM) — fetches & summarises recent news
6. SentimentAgent (LLM) — RSS feeds sentiment, hype/accumulation detection
7. UnicornDetectorAgent (LLM) — small cap, emerging sector, founder-led scoring
8. RiskAgent — red flags, governance, debt traps
9. Orchestrator (LLM) — final synthesis: rating, category, bull/bear case

**Path Parameter:**
| Param | Type | Description |
|---|---|---|
| `ticker` | string | NSE stock symbol (e.g., `RELIANCE`, `INFY`, `TCS`) |

**Request Body:**
```json
{
  "ticker": "RELIANCE",
  "current_price": 2850.50,
  "market_cap_cr": 1930000,
  "business_description": "Reliance Industries is India's largest conglomerate...",
  "eps": 96.0,
  "book_value_per_share": 850.0,
  "debt_cr": 312000,
  "cash_cr": 180000,
  "ebitda_cr": 160000,
  "fcf_cr": 45000,
  "shares_outstanding_cr": 677.0,
  "dividend_per_share": 10.0,
  "statements": [
    {
      "period": "2024",
      "period_type": "annual",
      "revenue_cr": 997025,
      "net_profit_cr": 79020,
      "total_equity_cr": 735000,
      "total_debt_cr": 312000,
      "capex_cr": 75000,
      "free_cash_flow_cr": 45000,
      "promoter_holding_pct": 50.3,
      "promoter_pledge_pct": 0.0
    }
  ]
}
```

**Field Reference:**
| Field | Required | Description |
|---|---|---|
| `ticker` | Yes | NSE symbol |
| `current_price` | Yes | Current market price in ₹ |
| `market_cap_cr` | Yes | Market capitalisation in ₹ crores |
| `business_description` | Yes | Min 20 chars — used by LLM agents for qualitative analysis |
| `eps` | No | Earnings per share in ₹ — needed to compute P/E ratio |
| `book_value_per_share` | No | Book value per share in ₹ — needed for P/B ratio |
| `debt_cr` | No | Total debt in ₹ crores (default: 0) |
| `cash_cr` | No | Cash & equivalents in ₹ crores (default: 0) |
| `ebitda_cr` | No | EBITDA in ₹ crores — needed for EV/EBITDA |
| `fcf_cr` | No | Free cash flow in ₹ crores — needed for DCF |
| `shares_outstanding_cr` | No | Shares outstanding in crores (default: 1.0) |
| `dividend_per_share` | No | Annual dividend per share in ₹ (default: 0) |
| `statements` | No | Array of annual/quarterly financial statements — needed for CAGR, ROE, D/E |

**Statement object fields:**
| Field | Description |
|---|---|
| `period` | e.g., `"2024"` or `"Q3FY24"` |
| `period_type` | `"annual"` or `"quarterly"` |
| `revenue_cr` | Revenue in ₹ crores |
| `net_profit_cr` | Net profit in ₹ crores |
| `total_equity_cr` | Shareholders equity in ₹ crores |
| `total_debt_cr` | Total debt in ₹ crores |
| `capex_cr` | Capital expenditure in ₹ crores |
| `free_cash_flow_cr` | FCF in ₹ crores |
| `promoter_holding_pct` | Promoter holding % |
| `promoter_pledge_pct` | Pledged promoter shares % |

**Response:**
```json
{
  "ticker": "RELIANCE",
  "current_price": 2850.5,
  "market_cap_cr": 1930000,

  "financial_strength_score": 7.8,
  "growth_score": 8.0,
  "valuation_score": 5.5,
  "moat_score": 8.2,
  "fisher_score": 7.5,
  "unicorn_score": 4.5,
  "sentiment_score": 6.5,
  "risk_score": 1.0,

  "pe_ratio": 29.7,
  "pb_ratio": 3.35,
  "ev_ebitda": 12.4,
  "peg_ratio": 1.2,
  "dividend_yield": 0.0035,
  "dcf_intrinsic_value": 3200.0,

  "roe": 0.185,
  "debt_equity": 0.42,
  "revenue_cagr_3y": 0.15,
  "profit_cagr_3y": 0.12,
  "fcf_cr": 45000,
  "promoter_holding_pct": 50.3,
  "promoter_pledge_pct": 0.0,

  "red_flags": [],
  "news_sentiment": "Positive",
  "news_summary": "Reliance reported strong Q3 results...",
  "moat_summary": "Reliance has a dominant distribution network and strong brand...",
  "fisher_summary": "Management has a clear long-term vision with Jio and retail...",
  "ten_x_potential": false,
  "growth_ceiling": "medium",
  "scuttlebutt_signals": ["Jio subscriber growth", "Retail EBITDA expansion"],

  "unicorn_summary": "Large cap — limited unicorn upside but strong emerging digital theme.",
  "emerging_themes": ["digital infrastructure"],
  "unicorn_size": "large_cap",
  "ten_x_candidate": false,
  "watch_triggers": [],

  "market_sentiment": "Bullish",
  "hype_detected": false,
  "accumulation_signal": true,
  "retail_buzz_level": "High",

  "business_summary": "Reliance Industries is India's largest private sector company...",
  "bull_case": ["Jio subscriber growth", "Retail EBITDA expanding", "Strong FCF"],
  "bear_case": ["High debt", "Capex-heavy business model"],
  "ideal_investor_type": "Long-term value investor with 5+ year horizon",
  "final_rating": "Strong Research Candidate",
  "confidence_pct": 78.0,
  "category": "long_term_compounder",

  "disclaimer": "This is educational research, not financial advice..."
}
```

**Ratings:**
| Rating | Meaning |
|---|---|
| `Strong Research Candidate` | High quality across financials, moat, valuation, governance |
| `Watch` | Some positives but needs monitoring |
| `Avoid` | Red flags present — do not invest |

**Categories:**
| Category | Meaning |
|---|---|
| `long_term_compounder` | Buffett/Fisher quality — hold for 10+ years |
| `undervalued_value` | Graham-style value play |
| `turnaround` | Recovering from temporary difficulty |
| `dividend_income` | Steady yield payer |
| `momentum_risky` | High growth, elevated risk |
| `avoid_watchlist` | Red flags — monitor only |

---

## 2. Philip Fisher Analysis

### `POST /api/v1/research/fisher/{ticker}`

Standalone Philip Fisher analysis. Scores a company on 7 Fisher dimensions using Claude LLM. Use this when you want Fisher-specific insights without running the full pipeline.

**Fisher dimensions scored:**
- `rd_innovation` — R&D investment and new product pipeline
- `sales_organisation` — Sales force strength and effectiveness
- `profit_margins` — Industry-leading and improving margins
- `management_integrity` — Honest communication, promises kept
- `management_vision` — Long-term vision and execution track record
- `employee_relations` — Talent attraction and retention
- `future_monopoly` — Potential to dominate the sector

**Request Body:**
```json
{
  "ticker": "DIXON",
  "business_description": "Dixon Technologies is India's largest EMS company...",
  "revenue_cagr_3y": 0.45,
  "profit_cagr_3y": 0.50,
  "roe": 0.22
}
```

**Response:**
```json
{
  "ticker": "DIXON",
  "fisher_score": 8.1,
  "dimension_scores": {
    "rd_innovation": 7.0,
    "sales_organisation": 8.0,
    "profit_margins": 7.5,
    "management_integrity": 9.0,
    "management_vision": 8.5,
    "employee_relations": 7.5,
    "future_monopoly": 8.0
  },
  "fisher_summary": "Dixon has strong execution and is riding the PLI scheme tailwind...",
  "scuttlebutt_signals": ["Consistent R&D investment", "Top talent from global OEMs"],
  "growth_ceiling": "high",
  "ten_x_potential": true
}
```

---

## 3. Market Sentiment

### `GET /api/v1/research/sentiment/{ticker}`

Fetches live sentiment from public RSS feeds (Moneycontrol, Economic Times, LiveMint) and analyses them with Claude LLM. No API key required for RSS — LLM key improves analysis quality.

**Path Parameter:**
| Param | Type | Description |
|---|---|---|
| `ticker` | string | NSE symbol to search for in news feeds |

**Example:** `GET /api/v1/research/sentiment/RELIANCE`

**Response:**
```json
{
  "ticker": "RELIANCE",
  "overall_sentiment": "Bullish",
  "hype_detected": false,
  "fear_detected": false,
  "accumulation_signal": true,
  "retail_buzz_level": "High",
  "analyst_bias": "Positive",
  "sentiment_score": 7.5,
  "key_signals": ["Strong earnings beat", "FII buying increasing"],
  "contrarian_note": "Market may be underestimating capex cycle risk.",
  "headline_count": 12
}
```

**Sentiment values:** `Bullish` | `Bearish` | `Neutral` | `Mixed`  
**Buzz levels:** `Low` | `Medium` | `High`

---

## 4. Unicorn Detection

### `POST /api/v1/research/unicorn/{ticker}`

Identifies if a stock has "unicorn" potential — small/mid cap, founder-led, emerging sector, high growth. Useful for finding the next 10x opportunity before the market notices.

**Scoring factors:**
- Quantitative: market cap < ₹5,000 Cr (small cap), revenue CAGR > 25%, ROE > 20%, high promoter holding
- Qualitative (LLM): TAM size, founder quality, tech adoption, sector tailwind, disruption potential
- 17+ emerging sector tailwinds tracked: defense, AI, EV, renewable, semiconductor, fintech, etc.

**Request Body:**
```json
{
  "ticker": "IDEAFORGE",
  "business_description": "ideaForge is India's leading drone manufacturer for defense and surveillance...",
  "market_cap_cr": 2800,
  "revenue_cagr_3y": 0.55,
  "profit_cagr_3y": 0.40,
  "roe": 0.18,
  "debt_equity": 0.05,
  "promoter_holding_pct": 52.0
}
```

**Response:**
```json
{
  "ticker": "IDEAFORGE",
  "unicorn_score": 8.7,
  "size_label": "small_cap",
  "dimension_scores": {
    "market_size_opportunity": 9.0,
    "founder_quality": 8.5,
    "tech_adoption": 9.0,
    "sector_tailwind": 9.5,
    "competitive_position": 8.0,
    "scalability": 7.5,
    "disruption_potential": 8.5
  },
  "unicorn_summary": "ideaForge is the clear market leader in defense drones in India...",
  "emerging_themes": ["defense indigenisation", "AI infrastructure", "aerospace"],
  "quant_flags": [
    "Small cap — high growth potential",
    "Strong revenue CAGR: 55.0%",
    "High ROE: 18.0%",
    "High promoter holding: 52.0% — founder alignment",
    "Debt-free or near debt-free"
  ],
  "risk_of_being_early": "Low",
  "watch_triggers": ["Defense order book > ₹500 Cr", "Export order wins", "New product line launch"],
  "ten_x_candidate": true
}
```

**`size_label` values:** `small_cap` (< ₹5,000 Cr) | `mid_cap` (₹5,000–20,000 Cr) | `large_cap` (> ₹20,000 Cr)

---

## 5. Daily Morning Report

### `POST /api/v1/report/daily`

The flagship endpoint. Runs the full 9-agent research pipeline on every stock in your watchlist and produces a ranked morning report with **Top 3 picks per category** — exactly like a professional research desk morning note.

**Categories in the report:**
| Category | Ranking Logic |
|---|---|
| `top_buffett_stocks` | ROE × moat score × (10 − risk score) × financial strength |
| `top_growth_stocks` | Revenue CAGR + profit CAGR + growth score + PEG |
| `top_small_cap_opportunities` | Unicorn score + small cap bonus + low risk |
| `top_emerging_theme_stocks` | Unicorn score + number of emerging themes + sentiment |
| `top_dividend_stocks` | Dividend yield × 2 + financial strength + low risk |
| `top_fisher_stocks` | Fisher score + 10x potential bonus + growth ceiling |
| `stocks_to_avoid` | Risk score + number of red flags (highest = most dangerous) |

**Request Body:**
```json
{
  "watchlist": [
    {
      "ticker": "RELIANCE",
      "current_price": 2850.50,
      "market_cap_cr": 1930000,
      "business_description": "Reliance Industries is India's largest conglomerate...",
      "eps": 96.0,
      "book_value_per_share": 850.0,
      "debt_cr": 312000,
      "cash_cr": 180000,
      "ebitda_cr": 160000,
      "fcf_cr": 45000,
      "dividend_per_share": 10.0
    },
    {
      "ticker": "DIXON",
      "current_price": 14500,
      "market_cap_cr": 8700,
      "business_description": "Dixon Technologies is India's largest EMS company...",
      "eps": 120.0,
      "fcf_cr": 200,
      "shares_outstanding_cr": 0.60
    }
  ]
}
```

**Response:**
```json
{
  "generated_at": "2026-06-07T06:00:00Z",
  "stocks_analysed": 2,

  "top_buffett_stocks": [
    {
      "ticker": "RELIANCE",
      "final_rating": "Strong Research Candidate",
      "category": "long_term_compounder",
      "score": 14.2,
      "current_price": 2850.5,
      "key_metrics": {
        "roe_pct": 18.5,
        "revenue_cagr_3y_pct": 15.0,
        "moat_score": 8.2,
        "fisher_score": 7.5,
        "unicorn_score": 4.5,
        "risk_score": 1.0,
        "pe_ratio": 29.7,
        "dividend_yield_pct": 0.35,
        "emerging_themes": ["digital infrastructure"],
        "ten_x_potential": false
      },
      "synopsis": "Reliance Industries is India's largest private sector company...",
      "bull_case": ["Jio subscriber growth", "Retail EBITDA expanding"],
      "bear_case": ["High debt", "Capex-heavy model"],
      "red_flags": []
    }
  ],

  "top_growth_stocks": [...],
  "top_small_cap_opportunities": [...],
  "top_emerging_theme_stocks": [...],
  "top_dividend_stocks": [...],
  "top_fisher_stocks": [...],

  "stocks_to_avoid": [
    {
      "ticker": "BADCO",
      "score": 9.0,
      "red_flags": ["high_debt", "governance_issue"],
      "bear_case": ["Debt/Equity ratio > 2.0", "SEBI action pending"]
    }
  ],

  "portfolio_rebalancing_note": "Review stocks_to_avoid against your current holdings...",
  "disclaimer": "This is educational research, not financial advice..."
}
```

---

## 6. Preview Order

### `POST /api/v1/orders/preview`

Previews a BUY or SELL order — calculates estimated cost, validates the order, and checks available funds. **Does not execute anything.** Safe to call at any time.

**Request Body:**
```json
{
  "ticker": "INFY",
  "side": "BUY",
  "quantity": 10,
  "price": 1850.00,
  "order_type": "LIMIT",
  "rationale": "Attractive valuation after Q3 dip",
  "available_funds": 25000.0
}
```

**Field Reference:**
| Field | Required | Values | Description |
|---|---|---|---|
| `ticker` | Yes | Any NSE symbol | Stock to trade |
| `side` | Yes | `BUY` or `SELL` | Direction |
| `quantity` | Yes | Integer > 0 | Number of shares |
| `price` | No | Float > 0 | Limit price (required for LIMIT/SL orders) |
| `order_type` | No | `LIMIT` \| `MARKET` \| `SL` \| `SL-M` | Default: `LIMIT` |
| `rationale` | No | String | Your reason for the trade (logged for audit) |
| `available_funds` | No | Float | Used to check if order fits within budget |

**Response:** Order preview with estimated total cost, validation status, and warnings.

---

## 7. Place Order

### `POST /api/v1/orders/place`

Places a paper or live order. **Requires `user_confirmed: true`** — a safety gate to prevent accidental execution.

- **Paper trading mode** (default, `PAPER_TRADING=true` in `.env`): order is logged locally, nothing is sent to broker.
- **Live mode** (`PAPER_TRADING=false`): order is routed to the configured broker (Zerodha/Upstox/Angel/Dhan).

**Request Body:**
```json
{
  "ticker": "INFY",
  "side": "BUY",
  "quantity": 10,
  "price": 1850.00,
  "order_type": "LIMIT",
  "rationale": "Attractive valuation after Q3 dip",
  "user_confirmed": true,
  "available_funds": 25000.0
}
```

> ⚠️ If `user_confirmed: false`, the order will be **rejected** with a clear error message.

---

## 8. Paper Trading Log

### `GET /api/v1/orders/paper-log`

Returns the full history of all paper trades placed in the current session.

**Example:** `GET /api/v1/orders/paper-log`

**Response:**
```json
{
  "orders": [
    {
      "ticker": "INFY",
      "side": "BUY",
      "quantity": 10,
      "price": 1850.0,
      "order_type": "LIMIT",
      "status": "paper_executed",
      "timestamp": "2026-06-07T06:15:00Z",
      "rationale": "Attractive valuation after Q3 dip"
    }
  ],
  "disclaimer": "This is educational research, not financial advice..."
}
```

---

## 9. Portfolio Allocation Suggestion

### `POST /api/v1/portfolio/suggest?total_investment=500000`

Suggests how to allocate a given investment amount across asset classes and stock categories based on a user's risk profile. Uses research reports (from `/research/{ticker}`) to weight stock-specific allocations.

**Query Parameter:**
| Param | Required | Description |
|---|---|---|
| `total_investment` | Yes | Total amount to invest in ₹ |

**Request Body:**
```json
{
  "user_profile": {
    "user_id": "user123",
    "risk_appetite": "moderate",
    "investment_horizon_years": 7,
    "emergency_fund_months": 6,
    "monthly_income_band": "2L-5L",
    "existing_holdings": []
  },
  "research_reports": []
}
```

**`risk_appetite` values:** `conservative` | `moderate` | `aggressive`

**Response:** Allocation bands per category (equity/debt split, sector weights, suggested position sizes) with disclaimer.

---

## 10. Stock Categories

### `GET /api/v1/categories`

Returns the 6 classification categories used by the research system.

**Example:** `GET /api/v1/categories`

**Response:**
```json
{
  "categories": [
    {"id": "long_term_compounder", "name": "Long-term Compounders", "description": "High-quality businesses with durable moats"},
    {"id": "undervalued_value", "name": "Undervalued Value Stocks", "description": "Trading below intrinsic value"},
    {"id": "turnaround", "name": "Turnaround Candidates", "description": "Recovering from temporary difficulties"},
    {"id": "dividend_income", "name": "Dividend / Income Stocks", "description": "Steady dividend payers"},
    {"id": "momentum_risky", "name": "Momentum (Risky)", "description": "Strong momentum but elevated risk"},
    {"id": "avoid_watchlist", "name": "Avoid / Watchlist", "description": "Red flags present — monitor only"}
  ],
  "disclaimer": "..."
}
```

---

## 11. Disclaimer

### `GET /api/v1/disclaimer`

Returns the standard SEBI compliance disclaimer. Included in every response but also available standalone.

**Example:** `GET /api/v1/disclaimer`

---

## Error Responses

All endpoints return standard HTTP error codes:

| Code | Meaning |
|---|---|
| `400` | Invalid input — ticker format, missing required field, validation error |
| `422` | Request body schema mismatch (Pydantic validation) |
| `500` | Internal pipeline failure — check server logs |

**Error body:**
```json
{
  "detail": "Description of what went wrong"
}
```

---

## Recommended Usage Flow

```
1. Screen stocks:
   POST /research/{ticker}    ← for each stock you're interested in

2. Deep dive on promising ones:
   POST /research/fisher/{ticker}     ← growth & vision analysis
   GET  /research/sentiment/{ticker}  ← current market mood
   POST /research/unicorn/{ticker}    ← 10x potential check

3. Run morning report on your watchlist:
   POST /report/daily                 ← Top 3 per category

4. Build your portfolio:
   POST /portfolio/suggest            ← allocation bands

5. Execute (paper first):
   POST /orders/preview               ← check before placing
   POST /orders/place                 ← user_confirmed: true required
   GET  /orders/paper-log             ← review what you've done
```

---

## Running the API

```bash
# FastAPI (REST + Swagger)
uvicorn src.api.main:app --host 0.0.0.0 --port 8080 --reload

# Streamlit dashboard (alternative UI)
streamlit run streamlit_app.py
# Opens at http://localhost:8501
```

*Swagger UI available at `http://localhost:8080/docs` — all endpoints are fully interactive there.*
