# Business Test Case Report
**Generated:** 2026-08-16 14:20 UTC  
**Total:** 420 | **✅ Passed:** 420 | **❌ Failed:** 0 | **⏭ Skipped:** 0

> This is educational research software. All tests validate research and safety logic — not financial advice.

## ✅ API Endpoints (17/17 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test health returns ok | ✅ PASSED | 5.0ms |
| 2 | test categories returns six categories | ✅ PASSED | 4.2ms |
| 3 | test categories has disclaimer | ✅ PASSED | 3.4ms |
| 4 | test disclaimer endpoint | ✅ PASSED | 3.0ms |
| 5 | test order preview returns preview | ✅ PASSED | 5.5ms |
| 6 | test order preview shows paper trade mode | ✅ PASSED | 3.1ms |
| 7 | test order place rejected without confirmation | ✅ PASSED | 3.4ms |
| 8 | test order place accepted with confirmation | ✅ PASSED | 3.5ms |
| 9 | test order place rejected insufficient funds | ✅ PASSED | 3.1ms |
| 10 | test order side validation | ✅ PASSED | 2.1ms |
| 11 | test paper log returns list | ✅ PASSED | 2.7ms |
| 12 | test research returns 200 | ✅ PASSED | 1204.8ms |
| 13 | test research contains disclaimer | ✅ PASSED | 1153.1ms |
| 14 | test research invalid ticker in body returns 400 | ✅ PASSED | 80.8ms |
| 15 | test research scores in range | ✅ PASSED | 1176.2ms |
| 16 | test research 500 on unexpected error | ✅ PASSED | 5.0ms |
| 17 | test research 400 on value error | ✅ PASSED | 3.7ms |

## ✅ Audit & Prompt Versioning (8/8 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test returns string | ✅ PASSED | 2.4ms |
| 2 | test returns unknown on failure | ✅ PASSED | 0.7ms |
| 3 | test record change creates prompt file | ✅ PASSED | 3.4ms |
| 4 | test record change content includes reason | ✅ PASSED | 2.6ms |
| 5 | test record change increments version | ✅ PASSED | 4.6ms |
| 6 | test changelog is updated | ✅ PASSED | 2.6ms |
| 7 | test changed files listed in prompt | ✅ PASSED | 2.4ms |
| 8 | test backtest result included when provided | ✅ PASSED | 2.2ms |

## ✅ Broker & Order Execution (29/29 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test valid order request | ✅ PASSED | 0.2ms |
| 2 | test ticker normalised to uppercase | ✅ PASSED | 0.1ms |
| 3 | test invalid ticker raises | ✅ PASSED | 0.1ms |
| 4 | test invalid quantity raises | ✅ PASSED | 0.1ms |
| 5 | test zero quantity raises | ✅ PASSED | 0.1ms |
| 6 | test negative price raises | ✅ PASSED | 0.1ms |
| 7 | test preview contains all fields | ✅ PASSED | 0.1ms |
| 8 | test preview estimated value correct | ✅ PASSED | 0.1ms |
| 9 | test is paper trading by default | ✅ PASSED | 0.9ms |
| 10 | test order rejected without confirmation | ✅ PASSED | 0.7ms |
| 11 | test paper order placed with confirmation | ✅ PASSED | 1.0ms |
| 12 | test insufficient funds rejected | ✅ PASSED | 0.6ms |
| 13 | test paper trade log records order | ✅ PASSED | 0.6ms |
| 14 | test multiple orders in log | ✅ PASSED | 1.0ms |
| 15 | test preview shows paper trade mode | ✅ PASSED | 0.6ms |
| 16 | test cancel paper trade with confirmation | ✅ PASSED | 0.6ms |
| 17 | test cancel without confirmation rejected | ✅ PASSED | 0.6ms |
| 18 | test disclaimer always in preview | ✅ PASSED | 0.5ms |
| 19 | test all four brokers registered | ✅ PASSED | 0.1ms |
| 20 | test create returns correct connector type[zerodha-ZerodhaConnector] | ✅ PASSED | 0.1ms |
| 21 | test create returns correct connector type[upstox-UpstoxConnector] | ✅ PASSED | 0.1ms |
| 22 | test create returns correct connector type[angelone-AngelOneConnector] | ✅ PASSED | 0.1ms |
| 23 | test create returns correct connector type[dhan-DhanConnector] | ✅ PASSED | 0.1ms |
| 24 | test create unknown broker raises value error | ✅ PASSED | 0.1ms |
| 25 | test all connectors are broker connector subclasses | ✅ PASSED | 0.2ms |
| 26 | test connector carries credentials from broker config | ✅ PASSED | 0.1ms |
| 27 | test unimplemented holdings raises not implemented | ✅ PASSED | 0.1ms |
| 28 | test default active broker | ✅ PASSED | 0.1ms |
| 29 | test active broker env var overrides yaml | ✅ PASSED | 13.1ms |

## ✅ Coverage Gap Tests (2/2 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test get logger returns same instance on repeat call | ✅ PASSED | 0.2ms |
| 2 | test get logger custom level | ✅ PASSED | 0.1ms |

## ✅ Data Collection (26/26 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test fetch historical prices general exception returns empty | ✅ PASSED | 49.8ms |
| 2 | test fetch nse stock list returns list on success | ✅ PASSED | 1.2ms |
| 3 | test fetch nse stock list returns empty on error | ✅ PASSED | 0.9ms |
| 4 | test fetch nse stock list stores source url | ✅ PASSED | 1.2ms |
| 5 | test fetch financials screener returns ticker | ✅ PASSED | 0.4ms |
| 6 | test fetch historical prices no yfinance returns empty | ✅ PASSED | 0.9ms |
| 7 | test close does not raise | ✅ PASSED | 0.2ms |
| 8 | test validate ticker in fetch financials | ✅ PASSED | 0.2ms |
| 9 | test fetch current ipos normalizes fields | ✅ PASSED | 1.2ms |
| 10 | test fetch current ipos returns empty on error | ✅ PASSED | 0.8ms |
| 11 | test fetch current ipos handles bare list response | ✅ PASSED | 1.5ms |
| 12 | test fetch upcoming ipos marks status upcoming | ✅ PASSED | 1.6ms |
| 13 | test fetch recently listed ipos filters by lookback window | ✅ PASSED | 3.2ms |
| 14 | test fetch recently listed ipos computes days since listing | ✅ PASSED | 1.9ms |
| 15 | test fetch recently listed ipos uses config default months | ✅ PASSED | 1.7ms |
| 16 | test fetch recently listed ipos keeps records with unparseable date | ✅ PASSED | 2.3ms |
| 17 | test parse date handles multiple formats[01-Jan-2026-expected0] | ✅ PASSED | 0.2ms |
| 18 | test parse date handles multiple formats[2026-01-01-expected1] | ✅ PASSED | 0.2ms |
| 19 | test parse date handles multiple formats[01/01/2026-expected2] | ✅ PASSED | 0.2ms |
| 20 | test parse date handles multiple formats[garbage-None] | ✅ PASSED | 0.2ms |
| 21 | test parse date handles multiple formats[None-None] | ✅ PASSED | 0.2ms |
| 22 | test close does not raise | ✅ PASSED | 0.2ms |
| 23 | test hunt delegates to unicorn hunter and merges ipo metadata | ✅ PASSED | 0.8ms |
| 24 | test analyze with mock data | ✅ PASSED | 409.5ms |
| 25 | test analyze empty dataframe | ✅ PASSED | 1.2ms |
| 26 | test compute trends insufficient data | ✅ PASSED | 0.1ms |

## ✅ Fundamental Analysis (48/48 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test fundamental roe tiers match old thresholds | ✅ PASSED | 0.1ms |
| 2 | test compute roce normal | ✅ PASSED | 0.1ms |
| 3 | test compute roce zero capital employed | ✅ PASSED | 0.1ms |
| 4 | test compute roce negative capital employed | ✅ PASSED | 0.1ms |
| 5 | test score de between 1 and 2 | ✅ PASSED | 0.1ms |
| 6 | test score de between 0 and 1 | ✅ PASSED | 0.1ms |
| 7 | test score de none | ✅ PASSED | 0.1ms |
| 8 | test score fcf zero revenue | ✅ PASSED | 0.1ms |
| 9 | test score fcf medium | ✅ PASSED | 0.1ms |
| 10 | test score fcf low positive | ✅ PASSED | 0.1ms |
| 11 | test score fcf negative | ✅ PASSED | 0.1ms |
| 12 | test score revenue cagr 15pct | ✅ PASSED | 0.1ms |
| 13 | test score revenue cagr 10pct | ✅ PASSED | 0.1ms |
| 14 | test score revenue cagr 5pct | ✅ PASSED | 0.1ms |
| 15 | test score revenue cagr low positive | ✅ PASSED | 0.1ms |
| 16 | test profit cagr negative start returns none | ✅ PASSED | 0.1ms |
| 17 | test revenue cagr insufficient data | ✅ PASSED | 0.1ms |
| 18 | test overall score all none | ✅ PASSED | 0.1ms |
| 19 | test revenue cagr returns value when enough data | ✅ PASSED | 0.1ms |
| 20 | test profit cagr none end value | ✅ PASSED | 0.1ms |
| 21 | test profit cagr valid returns value | ✅ PASSED | 0.1ms |
| 22 | test score roe between 10 and 15 | ✅ PASSED | 0.1ms |
| 23 | test score fcf between 5 and 10 | ✅ PASSED | 0.1ms |
| 24 | test cagr basic | ✅ PASSED | 0.1ms |
| 25 | test cagr zero start returns none | ✅ PASSED | 0.1ms |
| 26 | test cagr negative years returns none | ✅ PASSED | 0.1ms |
| 27 | test cagr none inputs | ✅ PASSED | 0.1ms |
| 28 | test compute roe normal | ✅ PASSED | 0.1ms |
| 29 | test compute roe zero equity | ✅ PASSED | 0.1ms |
| 30 | test compute debt equity normal | ✅ PASSED | 0.1ms |
| 31 | test compute debt equity zero equity | ✅ PASSED | 0.1ms |
| 32 | test compute interest coverage normal | ✅ PASSED | 0.1ms |
| 33 | test compute interest coverage zero interest | ✅ PASSED | 0.1ms |
| 34 | test compute fcf | ✅ PASSED | 0.1ms |
| 35 | test score roe excellent | ✅ PASSED | 0.1ms |
| 36 | test score roe good | ✅ PASSED | 0.1ms |
| 37 | test score roe minimum buffett | ✅ PASSED | 0.1ms |
| 38 | test score roe poor | ✅ PASSED | 0.1ms |
| 39 | test score roe negative | ✅ PASSED | 0.1ms |
| 40 | test score roe none | ✅ PASSED | 0.1ms |
| 41 | test score debt equity no debt | ✅ PASSED | 0.1ms |
| 42 | test score debt equity graham safe | ✅ PASSED | 0.1ms |
| 43 | test score debt equity high risk | ✅ PASSED | 0.1ms |
| 44 | test score revenue cagr high growth | ✅ PASSED | 0.1ms |
| 45 | test score revenue cagr negative | ✅ PASSED | 0.1ms |
| 46 | test analyze with statements | ✅ PASSED | 0.4ms |
| 47 | test analyze empty statements returns error | ✅ PASSED | 0.2ms |
| 48 | test analyze with quarterly only returns none cagr | ✅ PASSED | 0.1ms |

## ✅ General (125/125 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test all expected agents registered | ✅ PASSED | 0.1ms |
| 2 | test get returns registered class | ✅ PASSED | 0.1ms |
| 3 | test get unknown agent raises | ✅ PASSED | 0.2ms |
| 4 | test create instantiates agent | ✅ PASSED | 0.1ms |
| 5 | test enrichment agents expose output key and pipeline kwargs | ✅ PASSED | 0.1ms |
| 6 | test fisher pipeline kwargs pulls from context | ✅ PASSED | 0.1ms |
| 7 | test register decorator is idempotent on reimport | ✅ PASSED | 0.1ms |
| 8 | test override replaces scalar | ✅ PASSED | 0.1ms |
| 9 | test override merges nested dict | ✅ PASSED | 0.1ms |
| 10 | test override replaces list entirely | ✅ PASSED | 0.1ms |
| 11 | test base not mutated | ✅ PASSED | 0.1ms |
| 12 | test default only when env file missing | ✅ PASSED | 0.7ms |
| 13 | test env file overrides default | ✅ PASSED | 0.7ms |
| 14 | test env var interpolation | ✅ PASSED | 0.6ms |
| 15 | test disclaimer mentions sebi | ✅ PASSED | 0.1ms |
| 16 | test six categories | ✅ PASSED | 0.1ms |
| 17 | test default pipeline order | ✅ PASSED | 0.1ms |
| 18 | test paper trading env var parsed as bool | ✅ PASSED | 12.0ms |
| 19 | test get config is cached singleton | ✅ PASSED | 0.1ms |
| 20 | test hunt returns empty result when no ipos found | ✅ PASSED | 0.5ms |
| 21 | test hunt reranks by composite after recency bonus | ✅ PASSED | 0.8ms |
| 22 | test hunt respects top n truncation | ✅ PASSED | 1.0ms |
| 23 | test hunt uses explicit symbol list without fetching ipos | ✅ PASSED | 0.8ms |
| 24 | test close does not raise | ✅ PASSED | 0.2ms |
| 25 | test analyze with llm | ✅ PASSED | 64.6ms |
| 26 | test analyze fallback no llm | ✅ PASSED | 0.2ms |
| 27 | test llm failure falls back | ✅ PASSED | 48.2ms |
| 28 | test overall fisher score weights | ✅ PASSED | 0.1ms |
| 29 | test llm json parse error falls back | ✅ PASSED | 47.5ms |
| 30 | test analyze no optional financials | ✅ PASSED | 0.3ms |
| 31 | test analyze with llm no rss | ✅ PASSED | 107.3ms |
| 32 | test analyze fallback no llm | ✅ PASSED | 45.4ms |
| 33 | test rule based bullish | ✅ PASSED | 43.6ms |
| 34 | test rule based bearish | ✅ PASSED | 43.8ms |
| 35 | test rule based hype detection | ✅ PASSED | 44.0ms |
| 36 | test rss fetch network error handled | ✅ PASSED | 42.8ms |
| 37 | test rss fetch filters by ticker | ✅ PASSED | 47.5ms |
| 38 | test rss non 200 skipped | ✅ PASSED | 44.1ms |
| 39 | test analyze with extra articles | ✅ PASSED | 44.2ms |
| 40 | test llm failure falls back | ✅ PASSED | 87.4ms |
| 41 | test close | ✅ PASSED | 43.2ms |
| 42 | test analyze small cap with llm | ✅ PASSED | 45.4ms |
| 43 | test analyze large cap fallback | ✅ PASSED | 0.3ms |
| 44 | test quant filters small cap high growth | ✅ PASSED | 0.1ms |
| 45 | test quant filters large cap no growth | ✅ PASSED | 0.1ms |
| 46 | test sector tailwind defense | ✅ PASSED | 0.1ms |
| 47 | test sector tailwind no match | ✅ PASSED | 0.1ms |
| 48 | test sector tailwind multiple themes | ✅ PASSED | 0.1ms |
| 49 | test overall unicorn score clamps | ✅ PASSED | 0.1ms |
| 50 | test llm failure falls back | ✅ PASSED | 46.8ms |
| 51 | test mid cap label | ✅ PASSED | 0.4ms |
| 52 | test tailwind sectors not empty | ✅ PASSED | 0.1ms |
| 53 | test score buffett high roe | ✅ PASSED | 0.1ms |
| 54 | test score growth high cagr | ✅ PASSED | 0.1ms |
| 55 | test score small cap preferred | ✅ PASSED | 0.1ms |
| 56 | test score emerging theme more themes | ✅ PASSED | 0.1ms |
| 57 | test score dividend | ✅ PASSED | 0.1ms |
| 58 | test score fisher ten x | ✅ PASSED | 0.1ms |
| 59 | test score avoid more flags | ✅ PASSED | 0.1ms |
| 60 | test pick top returns n | ✅ PASSED | 0.2ms |
| 61 | test pick top excludes error reports | ✅ PASSED | 0.1ms |
| 62 | test pick top min score filter | ✅ PASSED | 0.1ms |
| 63 | test unicorn universe not empty | ✅ PASSED | 0.1ms |
| 64 | test unicorn universe no duplicates | ✅ PASSED | 0.1ms |
| 65 | test unicorn universe excludes large caps | ✅ PASSED | 0.1ms |
| 66 | test theme map has all expected themes | ✅ PASSED | 0.1ms |
| 67 | test detect themes defense | ✅ PASSED | 0.1ms |
| 68 | test detect themes solar | ✅ PASSED | 0.1ms |
| 69 | test detect themes multiple | ✅ PASSED | 0.1ms |
| 70 | test detect themes no match | ✅ PASSED | 0.1ms |
| 71 | test detect themes cdmo | ✅ PASSED | 0.1ms |
| 72 | test parse info basic | ✅ PASSED | 0.2ms |
| 73 | test parse info themes detected | ✅ PASSED | 0.1ms |
| 74 | test parse info de none when missing | ✅ PASSED | 0.1ms |
| 75 | test filter passes valid stock | ✅ PASSED | 0.1ms |
| 76 | test filter rejects too small mcap | ✅ PASSED | 0.1ms |
| 77 | test filter rejects large cap | ✅ PASSED | 0.1ms |
| 78 | test filter rejects low growth | ✅ PASSED | 0.1ms |
| 79 | test filter rejects high debt | ✅ PASSED | 0.1ms |
| 80 | test filter passes when growth none | ✅ PASSED | 0.1ms |
| 81 | test filter rejects penny stock | ✅ PASSED | 0.1ms |
| 82 | test unicorn score high growth | ✅ PASSED | 0.1ms |
| 83 | test unicorn score all keys present | ✅ PASSED | 0.1ms |
| 84 | test unicorn score capped at 10 | ✅ PASSED | 0.1ms |
| 85 | test unicorn score zero growth | ✅ PASSED | 0.1ms |
| 86 | test hunt returns expected keys | ✅ PASSED | 1.9ms |
| 87 | test hunt all filtered out | ✅ PASSED | 1.4ms |
| 88 | test hunt fetch failure counted | ✅ PASSED | 1.0ms |
| 89 | test hunt top n respected | ✅ PASSED | 3.8ms |
| 90 | test hunt sorted by composite | ✅ PASSED | 1.5ms |
| 91 | test hunt theme breakdown structure | ✅ PASSED | 1.0ms |
| 92 | test hunt progress callback called | ✅ PASSED | 1.4ms |
| 93 | test hunt uses unicorn universe by default | ✅ PASSED | 7.8ms |
| 94 | test hunt candidates have scores | ✅ PASSED | 1.3ms |
| 95 | test parse info converts units correctly | ✅ PASSED | 0.2ms |
| 96 | test prefilter passes good stock | ✅ PASSED | 0.1ms |
| 97 | test prefilter rejects micro cap | ✅ PASSED | 0.1ms |
| 98 | test prefilter rejects penny stock | ✅ PASSED | 0.1ms |
| 99 | test prefilter rejects no revenue | ✅ PASSED | 0.1ms |
| 100 | test prefilter rejects bad roe | ✅ PASSED | 0.1ms |
| 101 | test prefilter high de financial sector exempt | ✅ PASSED | 0.1ms |
| 102 | test quant score high quality stock | ✅ PASSED | 0.1ms |
| 103 | test screen with mocked fetch | ✅ PASSED | 1.7ms |
| 104 | test screen all fetch failures | ✅ PASSED | 1.2ms |
| 105 | test screen progress callback | ✅ PASSED | 1.1ms |
| 106 | test get symbol list fallback | ✅ PASSED | 35.6ms |
| 107 | test nifty100 fallback not empty | ✅ PASSED | 0.1ms |
| 108 | test parse info missing fields handled | ✅ PASSED | 0.1ms |
| 109 | test candidates sorted by composite score | ✅ PASSED | 0.1ms |
| 110 | test analyze returns error on fetch failure | ✅ PASSED | 0.4ms |
| 111 | test pct change calculation | ✅ PASSED | 0.1ms |
| 112 | test earnings quality score strong growth | ✅ PASSED | 0.1ms |
| 113 | test earnings quality score declining | ✅ PASSED | 0.1ms |
| 114 | test compute trends yoy | ✅ PASSED | 0.1ms |
| 115 | test safe cr returns none on bad df | ✅ PASSED | 0.1ms |
| 116 | test create and get job | ✅ PASSED | 0.1ms |
| 117 | test start job | ✅ PASSED | 0.1ms |
| 118 | test complete job | ✅ PASSED | 0.1ms |
| 119 | test fail job | ✅ PASSED | 0.1ms |
| 120 | test update progress | ✅ PASSED | 0.1ms |
| 121 | test get nonexistent job | ✅ PASSED | 0.1ms |
| 122 | test list jobs returns recent | ✅ PASSED | 0.1ms |
| 123 | test list jobs no result payload | ✅ PASSED | 0.1ms |
| 124 | test thread safety | ✅ PASSED | 4.7ms |
| 125 | test job returns copy not reference | ✅ PASSED | 0.1ms |

## ✅ Input Validation (27/27 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test validate ratio none returns none | ✅ PASSED | 0.1ms |
| 2 | test validate ratio valid float | ✅ PASSED | 0.1ms |
| 3 | test validate ratio valid int | ✅ PASSED | 0.1ms |
| 4 | test validate ratio non numeric raises | ✅ PASSED | 0.2ms |
| 5 | test validate score non numeric raises | ✅ PASSED | 0.1ms |
| 6 | test validate price non numeric raises | ✅ PASSED | 0.1ms |
| 7 | test validate quantity float truncated | ✅ PASSED | 0.1ms |
| 8 | test validate ratio zero valid | ✅ PASSED | 0.1ms |
| 9 | test valid ticker | ✅ PASSED | 0.1ms |
| 10 | test valid ticker with hyphen | ✅ PASSED | 0.1ms |
| 11 | test empty ticker raises | ✅ PASSED | 0.1ms |
| 12 | test none ticker raises | ✅ PASSED | 0.1ms |
| 13 | test whitespace stripped | ✅ PASSED | 0.1ms |
| 14 | test valid quantity | ✅ PASSED | 0.1ms |
| 15 | test string quantity converted | ✅ PASSED | 0.1ms |
| 16 | test zero raises | ✅ PASSED | 0.1ms |
| 17 | test negative raises | ✅ PASSED | 0.1ms |
| 18 | test non numeric raises | ✅ PASSED | 0.1ms |
| 19 | test valid price | ✅ PASSED | 0.1ms |
| 20 | test string price converted | ✅ PASSED | 0.1ms |
| 21 | test zero price raises | ✅ PASSED | 0.1ms |
| 22 | test negative price raises | ✅ PASSED | 0.1ms |
| 23 | test valid score 10 | ✅ PASSED | 0.1ms |
| 24 | test valid score 0 | ✅ PASSED | 0.1ms |
| 25 | test score above 10 raises | ✅ PASSED | 0.1ms |
| 26 | test score below 0 raises | ✅ PASSED | 0.1ms |
| 27 | test string score converted | ✅ PASSED | 0.1ms |

## ✅ Moat & Business Quality (19/19 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test moat pipeline kwargs defaults missing context gracefully | ✅ PASSED | 0.1ms |
| 2 | test moat weights sum to one | ✅ PASSED | 0.1ms |
| 3 | test fallback score returns all dimensions | ✅ PASSED | 1.3ms |
| 4 | test fallback score is 5 for all | ✅ PASSED | 0.9ms |
| 5 | test overall moat score in range | ✅ PASSED | 0.9ms |
| 6 | test overall moat score max inputs gives near 10 | ✅ PASSED | 0.9ms |
| 7 | test overall moat score min inputs gives 0 | ✅ PASSED | 0.5ms |
| 8 | test analyze without llm uses fallback | ✅ PASSED | 1.0ms |
| 9 | test analyze with llm success | ✅ PASSED | 56.0ms |
| 10 | test analyze with llm fallback on error | ✅ PASSED | 55.6ms |
| 11 | test analyze returns ticker | ✅ PASSED | 1.0ms |
| 12 | test analyze empty articles returns neutral | ✅ PASSED | 0.9ms |
| 13 | test keyword fallback positive sentiment | ✅ PASSED | 0.5ms |
| 14 | test keyword fallback negative sentiment | ✅ PASSED | 0.7ms |
| 15 | test keyword fallback mixed sentiment | ✅ PASSED | 0.6ms |
| 16 | test analyze without llm uses keyword fallback | ✅ PASSED | 0.5ms |
| 17 | test analyze with llm success | ✅ PASSED | 54.9ms |
| 18 | test analyze with llm fallback on error | ✅ PASSED | 45.5ms |
| 19 | test format articles caps at 20 | ✅ PASSED | 3.0ms |

## ✅ News & Sentiment (3/3 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test fetch news returns empty when no api key | ✅ PASSED | 49.5ms |
| 2 | test fetch news returns articles on success | ✅ PASSED | 1.9ms |
| 3 | test fetch news returns empty on error | ✅ PASSED | 0.6ms |

## ✅ Portfolio Construction (17/17 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test portfolio max single stock pct matches old constants | ✅ PASSED | 0.1ms |
| 2 | test sector weight clamped when sector nearly full | ✅ PASSED | 0.3ms |
| 3 | test weight zero triggers break | ✅ PASSED | 0.2ms |
| 4 | test portfolio suggest endpoint | ✅ PASSED | 4.9ms |
| 5 | test missing horizon flagged | ✅ PASSED | 0.1ms |
| 6 | test insufficient emergency fund flagged | ✅ PASSED | 0.1ms |
| 7 | test valid profile no issues | ✅ PASSED | 0.1ms |
| 8 | test exactly six months emergency fund accepted | ✅ PASSED | 0.1ms |
| 9 | test suggest allocation returns allocations | ✅ PASSED | 0.3ms |
| 10 | test allocation pct not exceed single stock limit | ✅ PASSED | 0.2ms |
| 11 | test allocation total not exceed 100 | ✅ PASSED | 0.2ms |
| 12 | test same sector concentration limited | ✅ PASSED | 0.2ms |
| 13 | test disclaimer always present | ✅ PASSED | 0.2ms |
| 14 | test incomplete profile returns error | ✅ PASSED | 0.1ms |
| 15 | test no eligible stocks returns message | ✅ PASSED | 0.1ms |
| 16 | test conservative profile lower single stock limit | ✅ PASSED | 0.2ms |
| 17 | test allocation amount matches pct | ✅ PASSED | 0.2ms |

## ✅ Research Orchestration (28/28 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test growth score between 15 and 20 | ✅ PASSED | 0.2ms |
| 2 | test growth score between 10 and 15 | ✅ PASSED | 0.2ms |
| 3 | test growth score between 5 and 10 | ✅ PASSED | 0.2ms |
| 4 | test growth score none values | ✅ PASSED | 0.2ms |
| 5 | test research returns all required keys | ✅ PASSED | 1249.8ms |
| 6 | test disclaimer always present | ✅ PASSED | 1113.2ms |
| 7 | test final rating is valid value | ✅ PASSED | 1065.5ms |
| 8 | test scores are in range | ✅ PASSED | 1013.8ms |
| 9 | test invalid ticker raises | ✅ PASSED | 91.8ms |
| 10 | test growth score high growth | ✅ PASSED | 90.3ms |
| 11 | test growth score low growth | ✅ PASSED | 91.6ms |
| 12 | test rule based synthesis strong candidate | ✅ PASSED | 92.3ms |
| 13 | test llm synthesis with mock | ✅ PASSED | 399.5ms |
| 14 | test llm synthesis falls back on error | ✅ PASSED | 480.1ms |
| 15 | test run single stock | ✅ PASSED | 140.1ms |
| 16 | test run failed stock included as error | ✅ PASSED | 88.7ms |
| 17 | test run multiple stocks | ✅ PASSED | 88.2ms |
| 18 | test report structure | ✅ PASSED | 94.9ms |
| 19 | test top pick structure | ✅ PASSED | 89.0ms |
| 20 | test run produces all category keys | ✅ PASSED | 76.4ms |
| 21 | test run stats populated | ✅ PASSED | 77.5ms |
| 22 | test run handles orchestrator failure | ✅ PASSED | 73.6ms |
| 23 | test run progress callback called | ✅ PASSED | 85.8ms |
| 24 | test run enriches report with earnings data | ✅ PASSED | 90.2ms |
| 25 | test lynch scoring | ✅ PASSED | 0.1ms |
| 26 | test lynch high peg scores lower | ✅ PASSED | 0.1ms |
| 27 | test pick top10 returns max 10 | ✅ PASSED | 0.2ms |
| 28 | test pick top10 structure | ✅ PASSED | 0.1ms |

## ✅ Risk Detection (26/26 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test risk score de above 3 | ✅ PASSED | 0.1ms |
| 2 | test risk score de between 2 and 3 | ✅ PASSED | 0.1ms |
| 3 | test risk score de none no extra penalty | ✅ PASSED | 0.1ms |
| 4 | test rule based synthesis avoid high risk | ✅ PASSED | 91.3ms |
| 5 | test score buffett high risk penalised | ✅ PASSED | 0.1ms |
| 6 | test avoid list excludes strong candidates with low risk | ✅ PASSED | 89.0ms |
| 7 | test missing risk appetite flagged | ✅ PASSED | 0.1ms |
| 8 | test high debt flag detected | ✅ PASSED | 0.2ms |
| 9 | test negative fcf flag detected | ✅ PASSED | 0.2ms |
| 10 | test high promoter pledge flag | ✅ PASSED | 0.2ms |
| 11 | test low promoter holding flag | ✅ PASSED | 0.1ms |
| 12 | test overvalued pe flag | ✅ PASSED | 0.2ms |
| 13 | test auditor change flag | ✅ PASSED | 0.2ms |
| 14 | test governance issue flag | ✅ PASSED | 0.2ms |
| 15 | test sudden price spike flag | ✅ PASSED | 0.2ms |
| 16 | test negative operating cash flow flag | ✅ PASSED | 0.1ms |
| 17 | test clean company no flags | ✅ PASSED | 0.1ms |
| 18 | test de exactly at threshold no flag | ✅ PASSED | 0.1ms |
| 19 | test pe exactly at threshold no flag | ✅ PASSED | 0.1ms |
| 20 | test risk score zero for no flags | ✅ PASSED | 0.1ms |
| 21 | test risk score severe flags higher | ✅ PASSED | 0.1ms |
| 22 | test risk score capped at 10 | ✅ PASSED | 0.1ms |
| 23 | test analyze returns all keys | ✅ PASSED | 0.3ms |
| 24 | test analyze high risk labeled correctly | ✅ PASSED | 0.2ms |
| 25 | test analyze low risk labeled correctly | ✅ PASSED | 0.2ms |
| 26 | test quant score risky stock | ✅ PASSED | 0.1ms |

## ✅ Valuation & DCF (45/45 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test valuation weights sum to one | ✅ PASSED | 0.1ms |
| 2 | test dividend yield zero price returns none | ✅ PASSED | 0.1ms |
| 3 | test dividend yield negative price returns none | ✅ PASSED | 0.1ms |
| 4 | test score pe between 20 and 30 | ✅ PASSED | 0.1ms |
| 5 | test score pe between 30 and 50 | ✅ PASSED | 0.1ms |
| 6 | test score pe none | ✅ PASSED | 0.1ms |
| 7 | test score pb between 1 and 1 5 | ✅ PASSED | 0.1ms |
| 8 | test score pb between 3 and 5 | ✅ PASSED | 0.1ms |
| 9 | test score pb none | ✅ PASSED | 0.1ms |
| 10 | test score peg between 1 and 1 5 | ✅ PASSED | 0.1ms |
| 11 | test score peg between 1 5 and 2 | ✅ PASSED | 0.1ms |
| 12 | test score peg none | ✅ PASSED | 0.1ms |
| 13 | test score margin of safety between 25 and 40 | ✅ PASSED | 0.1ms |
| 14 | test score margin of safety between 10 and 25 | ✅ PASSED | 0.1ms |
| 15 | test score margin of safety between 0 and 10 | ✅ PASSED | 0.1ms |
| 16 | test score margin of safety none intrinsic | ✅ PASSED | 0.1ms |
| 17 | test dcf zero shares uses default 1 | ✅ PASSED | 0.3ms |
| 18 | test score pe between 15 and 20 | ✅ PASSED | 0.1ms |
| 19 | test score pb between 1 5 and 3 | ✅ PASSED | 0.1ms |
| 20 | test score pb at or below 1 | ✅ PASSED | 0.1ms |
| 21 | test pe ratio normal | ✅ PASSED | 0.1ms |
| 22 | test pe ratio negative eps returns none | ✅ PASSED | 0.1ms |
| 23 | test pe ratio zero eps returns none | ✅ PASSED | 0.1ms |
| 24 | test pb ratio normal | ✅ PASSED | 0.1ms |
| 25 | test pb ratio zero book returns none | ✅ PASSED | 0.1ms |
| 26 | test ev ebitda normal | ✅ PASSED | 0.1ms |
| 27 | test ev ebitda zero ebitda returns none | ✅ PASSED | 0.1ms |
| 28 | test peg ratio normal | ✅ PASSED | 0.1ms |
| 29 | test peg ratio zero growth returns none | ✅ PASSED | 0.1ms |
| 30 | test dividend yield normal | ✅ PASSED | 0.1ms |
| 31 | test score pe graham value | ✅ PASSED | 0.1ms |
| 32 | test score pe very low | ✅ PASSED | 0.1ms |
| 33 | test score pe very high | ✅ PASSED | 0.1ms |
| 34 | test score pb graham attractive | ✅ PASSED | 0.1ms |
| 35 | test score pb expensive | ✅ PASSED | 0.1ms |
| 36 | test score peg lynch undervalued | ✅ PASSED | 0.1ms |
| 37 | test score peg overvalued | ✅ PASSED | 0.1ms |
| 38 | test score margin of safety deep value | ✅ PASSED | 0.1ms |
| 39 | test score margin of safety above intrinsic | ✅ PASSED | 0.1ms |
| 40 | test dcf positive fcf | ✅ PASSED | 0.4ms |
| 41 | test dcf negative fcf returns error | ✅ PASSED | 0.1ms |
| 42 | test dcf assumptions shown | ✅ PASSED | 0.2ms |
| 43 | test dcf custom margin of safety | ✅ PASSED | 0.2ms |
| 44 | test analyze returns all keys | ✅ PASSED | 0.2ms |
| 45 | test overall valuation score in range | ✅ PASSED | 0.1ms |
