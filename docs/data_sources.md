# Data Sources

## Allowed Sources

| Source | Type | Access Method | Notes |
|--------|------|---------------|-------|
| NSE India | Price, filings | Public API / CSV downloads | Respect ToS |
| BSE India | Price, filings | Public API / CSV downloads | Respect ToS |
| Zerodha Kite Connect | Price, orders | Official API (paid) | Requires broker account |
| Upstox API v2 | Price, orders | Official API | Requires broker account |
| Angel One SmartAPI | Price, orders | Official API | Requires broker account |
| DhanHQ API | Price, orders | Official API | Requires broker account |
| Fyers API | Price, orders | Official API | Requires broker account |
| ICICI Direct Breeze | Price, orders | Official API | Requires broker account |
| NewsAPI | News | REST API (key required) | Commercial license for production |
| SEBI EDGAR | Filings | Public | Disclosures, annual reports |
| RBI | Macro data | Public | Repo rate, CPI, IIP |
| Yahoo Finance (yfinance) | Historical prices | Python library | For backtesting only, check ToS |
| Screener.in | Financials | Manual / API if available | Personal use per ToS |

## Prohibited Actions

- Scraping any site that prohibits it in robots.txt or ToS
- Re-distributing raw exchange data commercially
- Using unofficial/leaked APIs
- Caching data beyond the API provider's allowed retention period
