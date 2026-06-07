# Compliance and Legal Rules

## SEBI Disclaimer (Required on Every Output)

> This is educational research, not financial advice. Consult a SEBI-registered investment adviser before investing.

## What This System Must Never Do

- Make guaranteed return claims
- Advise intraday trading, options, or F&O for beginners
- Execute real trades without explicit user confirmation
- Bypass SEBI, broker, or exchange rules
- Scrape data from websites that prohibit it
- Store API keys or credentials in source code
- Recommend a stock based on a single signal

## Broker API Rules

- Default mode is always **paper trading**
- Real order placement requires:
  1. User explicitly requests live trading
  2. Order preview shown (symbol, qty, price, side)
  3. Risk warning displayed
  4. Available funds verified
  5. User confirms again
  6. Order logged with timestamp and rationale

## Data Source Rules

- Only use NSE/BSE public data within their permitted use terms
- Respect rate limits on all broker APIs
- Do not re-distribute raw exchange data
- News content is for research summarization only

## Audit Requirements

Every production code change must produce:
1. An entry in `docs/CHANGELOG.md`
2. A prompt version file in `prompts/prompt_versions/`
3. Passing unit tests before merge
