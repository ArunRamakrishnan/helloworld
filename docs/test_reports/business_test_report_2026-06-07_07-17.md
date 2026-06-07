# Business Test Case Report
**Generated:** 2026-06-07 07:17 UTC  
**Total:** 333 | **✅ Passed:** 333 | **❌ Failed:** 0 | **⏭ Skipped:** 0

> This is educational research software. All tests validate research and safety logic — not financial advice.

## ✅ API Endpoints (17/17 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test health returns ok | ✅ PASSED | 5.0ms |
| 2 | test categories returns six categories | ✅ PASSED | 4.8ms |
| 3 | test categories has disclaimer | ✅ PASSED | 3.0ms |
| 4 | test disclaimer endpoint | ✅ PASSED | 2.9ms |
| 5 | test order preview returns preview | ✅ PASSED | 3.7ms |
| 6 | test order preview shows paper trade mode | ✅ PASSED | 3.2ms |
| 7 | test order place rejected without confirmation | ✅ PASSED | 4.0ms |
| 8 | test order place accepted with confirmation | ✅ PASSED | 3.4ms |
| 9 | test order place rejected insufficient funds | ✅ PASSED | 3.5ms |
| 10 | test order side validation | ✅ PASSED | 2.0ms |
| 11 | test paper log returns list | ✅ PASSED | 3.0ms |
| 12 | test research returns 200 | ✅ PASSED | 560.5ms |
| 13 | test research contains disclaimer | ✅ PASSED | 164.1ms |
| 14 | test research invalid ticker in body returns 400 | ✅ PASSED | 56.1ms |
| 15 | test research scores in range | ✅ PASSED | 150.2ms |
| 16 | test research 500 on unexpected error | ✅ PASSED | 5.1ms |
| 17 | test research 400 on value error | ✅ PASSED | 3.3ms |

## ✅ Audit & Prompt Versioning (8/8 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test returns string | ✅ PASSED | 2.8ms |
| 2 | test returns unknown on failure | ✅ PASSED | 0.7ms |
| 3 | test record change creates prompt file | ✅ PASSED | 3.3ms |
| 4 | test record change content includes reason | ✅ PASSED | 2.5ms |
| 5 | test record change increments version | ✅ PASSED | 5.0ms |
| 6 | test changelog is updated | ✅ PASSED | 2.8ms |
| 7 | test changed files listed in prompt | ✅ PASSED | 2.9ms |
| 8 | test backtest result included when provided | ✅ PASSED | 2.4ms |

## ✅ Broker & Order Execution (18/18 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test valid order request | ✅ PASSED | 0.2ms |
| 2 | test ticker normalised to uppercase | ✅ PASSED | 0.2ms |
| 3 | test invalid ticker raises | ✅ PASSED | 0.1ms |
| 4 | test invalid quantity raises | ✅ PASSED | 0.1ms |
| 5 | test zero quantity raises | ✅ PASSED | 0.1ms |
| 6 | test negative price raises | ✅ PASSED | 0.1ms |
| 7 | test preview contains all fields | ✅ PASSED | 0.1ms |
| 8 | test preview estimated value correct | ✅ PASSED | 0.1ms |
| 9 | test is paper trading by default | ✅ PASSED | 2.3ms |
| 10 | test order rejected without confirmation | ✅ PASSED | 0.7ms |
| 11 | test paper order placed with confirmation | ✅ PASSED | 0.7ms |
| 12 | test insufficient funds rejected | ✅ PASSED | 0.7ms |
| 13 | test paper trade log records order | ✅ PASSED | 0.6ms |
| 14 | test multiple orders in log | ✅ PASSED | 0.9ms |
| 15 | test preview shows paper trade mode | ✅ PASSED | 0.6ms |
| 16 | test cancel paper trade with confirmation | ✅ PASSED | 0.5ms |
| 17 | test cancel without confirmation rejected | ✅ PASSED | 0.6ms |
| 18 | test disclaimer always in preview | ✅ PASSED | 0.7ms |

## ✅ Coverage Gap Tests (2/2 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test get logger returns same instance on repeat call | ✅ PASSED | 0.2ms |
| 2 | test get logger custom level | ✅ PASSED | 0.1ms |

## ✅ Data Collection (11/11 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test fetch historical prices general exception returns empty | ✅ PASSED | 26.4ms |
| 2 | test fetch nse stock list returns list on success | ✅ PASSED | 1.3ms |
| 3 | test fetch nse stock list returns empty on error | ✅ PASSED | 0.8ms |
| 4 | test fetch nse stock list stores source url | ✅ PASSED | 2.0ms |
| 5 | test fetch financials screener returns ticker | ✅ PASSED | 0.3ms |
| 6 | test fetch historical prices no yfinance returns empty | ✅ PASSED | 0.7ms |
| 7 | test close does not raise | ✅ PASSED | 0.1ms |
| 8 | test validate ticker in fetch financials | ✅ PASSED | 0.2ms |
| 9 | test analyze with mock data | ✅ PASSED | 417.5ms |
| 10 | test analyze empty dataframe | ✅ PASSED | 0.7ms |
| 11 | test compute trends insufficient data | ✅ PASSED | 0.1ms |

## ✅ Fundamental Analysis (47/47 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test compute roce normal | ✅ PASSED | 0.1ms |
| 2 | test compute roce zero capital employed | ✅ PASSED | 0.1ms |
| 3 | test compute roce negative capital employed | ✅ PASSED | 0.1ms |
| 4 | test score de between 1 and 2 | ✅ PASSED | 0.1ms |
| 5 | test score de between 0 and 1 | ✅ PASSED | 0.1ms |
| 6 | test score de none | ✅ PASSED | 0.1ms |
| 7 | test score fcf zero revenue | ✅ PASSED | 0.1ms |
| 8 | test score fcf medium | ✅ PASSED | 0.1ms |
| 9 | test score fcf low positive | ✅ PASSED | 0.1ms |
| 10 | test score fcf negative | ✅ PASSED | 0.1ms |
| 11 | test score revenue cagr 15pct | ✅ PASSED | 0.1ms |
| 12 | test score revenue cagr 10pct | ✅ PASSED | 0.1ms |
| 13 | test score revenue cagr 5pct | ✅ PASSED | 0.1ms |
| 14 | test score revenue cagr low positive | ✅ PASSED | 0.1ms |
| 15 | test profit cagr negative start returns none | ✅ PASSED | 0.1ms |
| 16 | test revenue cagr insufficient data | ✅ PASSED | 0.1ms |
| 17 | test overall score all none | ✅ PASSED | 0.1ms |
| 18 | test revenue cagr returns value when enough data | ✅ PASSED | 0.1ms |
| 19 | test profit cagr none end value | ✅ PASSED | 0.1ms |
| 20 | test profit cagr valid returns value | ✅ PASSED | 0.1ms |
| 21 | test score roe between 10 and 15 | ✅ PASSED | 0.1ms |
| 22 | test score fcf between 5 and 10 | ✅ PASSED | 0.1ms |
| 23 | test cagr basic | ✅ PASSED | 0.1ms |
| 24 | test cagr zero start returns none | ✅ PASSED | 0.1ms |
| 25 | test cagr negative years returns none | ✅ PASSED | 0.1ms |
| 26 | test cagr none inputs | ✅ PASSED | 0.1ms |
| 27 | test compute roe normal | ✅ PASSED | 0.1ms |
| 28 | test compute roe zero equity | ✅ PASSED | 0.1ms |
| 29 | test compute debt equity normal | ✅ PASSED | 0.1ms |
| 30 | test compute debt equity zero equity | ✅ PASSED | 0.1ms |
| 31 | test compute interest coverage normal | ✅ PASSED | 0.1ms |
| 32 | test compute interest coverage zero interest | ✅ PASSED | 0.1ms |
| 33 | test compute fcf | ✅ PASSED | 0.1ms |
| 34 | test score roe excellent | ✅ PASSED | 0.1ms |
| 35 | test score roe good | ✅ PASSED | 0.1ms |
| 36 | test score roe minimum buffett | ✅ PASSED | 0.1ms |
| 37 | test score roe poor | ✅ PASSED | 0.1ms |
| 38 | test score roe negative | ✅ PASSED | 0.1ms |
| 39 | test score roe none | ✅ PASSED | 0.1ms |
| 40 | test score debt equity no debt | ✅ PASSED | 0.1ms |
| 41 | test score debt equity graham safe | ✅ PASSED | 0.1ms |
| 42 | test score debt equity high risk | ✅ PASSED | 0.1ms |
| 43 | test score revenue cagr high growth | ✅ PASSED | 0.1ms |
| 44 | test score revenue cagr negative | ✅ PASSED | 0.1ms |
| 45 | test analyze with statements | ✅ PASSED | 0.3ms |
| 46 | test analyze empty statements returns error | ✅ PASSED | 0.2ms |
| 47 | test analyze with quarterly only returns none cagr | ✅ PASSED | 0.2ms |

## ✅ General (69/69 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test analyze with llm | ✅ PASSED | 25.9ms |
| 2 | test analyze fallback no llm | ✅ PASSED | 0.3ms |
| 3 | test llm failure falls back | ✅ PASSED | 36.3ms |
| 4 | test overall fisher score weights | ✅ PASSED | 0.1ms |
| 5 | test llm json parse error falls back | ✅ PASSED | 30.4ms |
| 6 | test analyze no optional financials | ✅ PASSED | 0.2ms |
| 7 | test analyze with llm no rss | ✅ PASSED | 95.0ms |
| 8 | test analyze fallback no llm | ✅ PASSED | 26.7ms |
| 9 | test rule based bullish | ✅ PASSED | 24.5ms |
| 10 | test rule based bearish | ✅ PASSED | 24.9ms |
| 11 | test rule based hype detection | ✅ PASSED | 24.0ms |
| 12 | test rss fetch network error handled | ✅ PASSED | 23.7ms |
| 13 | test rss fetch filters by ticker | ✅ PASSED | 24.7ms |
| 14 | test rss non 200 skipped | ✅ PASSED | 25.1ms |
| 15 | test analyze with extra articles | ✅ PASSED | 24.1ms |
| 16 | test llm failure falls back | ✅ PASSED | 47.7ms |
| 17 | test close | ✅ PASSED | 23.8ms |
| 18 | test analyze small cap with llm | ✅ PASSED | 24.9ms |
| 19 | test analyze large cap fallback | ✅ PASSED | 0.2ms |
| 20 | test quant filters small cap high growth | ✅ PASSED | 0.1ms |
| 21 | test quant filters large cap no growth | ✅ PASSED | 0.1ms |
| 22 | test sector tailwind defense | ✅ PASSED | 0.2ms |
| 23 | test sector tailwind no match | ✅ PASSED | 0.1ms |
| 24 | test sector tailwind multiple themes | ✅ PASSED | 0.1ms |
| 25 | test overall unicorn score clamps | ✅ PASSED | 0.1ms |
| 26 | test llm failure falls back | ✅ PASSED | 24.6ms |
| 27 | test mid cap label | ✅ PASSED | 0.3ms |
| 28 | test tailwind sectors not empty | ✅ PASSED | 0.1ms |
| 29 | test score buffett high roe | ✅ PASSED | 0.1ms |
| 30 | test score growth high cagr | ✅ PASSED | 0.1ms |
| 31 | test score small cap preferred | ✅ PASSED | 0.1ms |
| 32 | test score emerging theme more themes | ✅ PASSED | 0.1ms |
| 33 | test score dividend | ✅ PASSED | 0.1ms |
| 34 | test score fisher ten x | ✅ PASSED | 0.1ms |
| 35 | test score avoid more flags | ✅ PASSED | 0.1ms |
| 36 | test pick top returns n | ✅ PASSED | 0.1ms |
| 37 | test pick top excludes error reports | ✅ PASSED | 0.1ms |
| 38 | test pick top min score filter | ✅ PASSED | 0.1ms |
| 39 | test parse info converts units correctly | ✅ PASSED | 0.2ms |
| 40 | test prefilter passes good stock | ✅ PASSED | 0.1ms |
| 41 | test prefilter rejects micro cap | ✅ PASSED | 0.1ms |
| 42 | test prefilter rejects penny stock | ✅ PASSED | 0.1ms |
| 43 | test prefilter rejects no revenue | ✅ PASSED | 0.1ms |
| 44 | test prefilter rejects bad roe | ✅ PASSED | 0.1ms |
| 45 | test prefilter high de financial sector exempt | ✅ PASSED | 0.1ms |
| 46 | test quant score high quality stock | ✅ PASSED | 0.1ms |
| 47 | test screen with mocked fetch | ✅ PASSED | 2.0ms |
| 48 | test screen all fetch failures | ✅ PASSED | 1.3ms |
| 49 | test screen progress callback | ✅ PASSED | 1.1ms |
| 50 | test get symbol list fallback | ✅ PASSED | 24.7ms |
| 51 | test nifty100 fallback not empty | ✅ PASSED | 0.1ms |
| 52 | test parse info missing fields handled | ✅ PASSED | 0.1ms |
| 53 | test candidates sorted by composite score | ✅ PASSED | 0.1ms |
| 54 | test analyze returns error on fetch failure | ✅ PASSED | 0.5ms |
| 55 | test pct change calculation | ✅ PASSED | 0.2ms |
| 56 | test earnings quality score strong growth | ✅ PASSED | 0.1ms |
| 57 | test earnings quality score declining | ✅ PASSED | 0.1ms |
| 58 | test compute trends yoy | ✅ PASSED | 0.1ms |
| 59 | test safe cr returns none on bad df | ✅ PASSED | 0.1ms |
| 60 | test create and get job | ✅ PASSED | 0.1ms |
| 61 | test start job | ✅ PASSED | 0.1ms |
| 62 | test complete job | ✅ PASSED | 0.1ms |
| 63 | test fail job | ✅ PASSED | 0.1ms |
| 64 | test update progress | ✅ PASSED | 0.1ms |
| 65 | test get nonexistent job | ✅ PASSED | 0.1ms |
| 66 | test list jobs returns recent | ✅ PASSED | 0.1ms |
| 67 | test list jobs no result payload | ✅ PASSED | 0.1ms |
| 68 | test thread safety | ✅ PASSED | 4.3ms |
| 69 | test job returns copy not reference | ✅ PASSED | 0.1ms |

## ✅ Input Validation (27/27 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test validate ratio none returns none | ✅ PASSED | 0.1ms |
| 2 | test validate ratio valid float | ✅ PASSED | 0.2ms |
| 3 | test validate ratio valid int | ✅ PASSED | 0.1ms |
| 4 | test validate ratio non numeric raises | ✅ PASSED | 0.1ms |
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

## ✅ Moat & Business Quality (17/17 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test fallback score returns all dimensions | ✅ PASSED | 0.6ms |
| 2 | test fallback score is 5 for all | ✅ PASSED | 0.6ms |
| 3 | test overall moat score in range | ✅ PASSED | 0.5ms |
| 4 | test overall moat score max inputs gives near 10 | ✅ PASSED | 0.5ms |
| 5 | test overall moat score min inputs gives 0 | ✅ PASSED | 0.6ms |
| 6 | test analyze without llm uses fallback | ✅ PASSED | 0.7ms |
| 7 | test analyze with llm success | ✅ PASSED | 27.6ms |
| 8 | test analyze with llm fallback on error | ✅ PASSED | 26.5ms |
| 9 | test analyze returns ticker | ✅ PASSED | 0.7ms |
| 10 | test analyze empty articles returns neutral | ✅ PASSED | 2.2ms |
| 11 | test keyword fallback positive sentiment | ✅ PASSED | 0.5ms |
| 12 | test keyword fallback negative sentiment | ✅ PASSED | 0.5ms |
| 13 | test keyword fallback mixed sentiment | ✅ PASSED | 0.7ms |
| 14 | test analyze without llm uses keyword fallback | ✅ PASSED | 0.6ms |
| 15 | test analyze with llm success | ✅ PASSED | 25.1ms |
| 16 | test analyze with llm fallback on error | ✅ PASSED | 24.8ms |
| 17 | test format articles caps at 20 | ✅ PASSED | 0.6ms |

## ✅ News & Sentiment (3/3 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test fetch news returns empty when no api key | ✅ PASSED | 29.6ms |
| 2 | test fetch news returns articles on success | ✅ PASSED | 1.0ms |
| 3 | test fetch news returns empty on error | ✅ PASSED | 0.6ms |

## ✅ Portfolio Construction (16/16 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test sector weight clamped when sector nearly full | ✅ PASSED | 0.2ms |
| 2 | test weight zero triggers break | ✅ PASSED | 0.2ms |
| 3 | test portfolio suggest endpoint | ✅ PASSED | 5.8ms |
| 4 | test missing horizon flagged | ✅ PASSED | 0.1ms |
| 5 | test insufficient emergency fund flagged | ✅ PASSED | 0.1ms |
| 6 | test valid profile no issues | ✅ PASSED | 0.1ms |
| 7 | test exactly six months emergency fund accepted | ✅ PASSED | 0.1ms |
| 8 | test suggest allocation returns allocations | ✅ PASSED | 0.2ms |
| 9 | test allocation pct not exceed single stock limit | ✅ PASSED | 0.2ms |
| 10 | test allocation total not exceed 100 | ✅ PASSED | 0.2ms |
| 11 | test same sector concentration limited | ✅ PASSED | 0.2ms |
| 12 | test disclaimer always present | ✅ PASSED | 0.2ms |
| 13 | test incomplete profile returns error | ✅ PASSED | 0.1ms |
| 14 | test no eligible stocks returns message | ✅ PASSED | 0.1ms |
| 15 | test conservative profile lower single stock limit | ✅ PASSED | 0.2ms |
| 16 | test allocation amount matches pct | ✅ PASSED | 0.2ms |

## ✅ Research Orchestration (28/28 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test growth score between 15 and 20 | ✅ PASSED | 0.1ms |
| 2 | test growth score between 10 and 15 | ✅ PASSED | 0.2ms |
| 3 | test growth score between 5 and 10 | ✅ PASSED | 0.1ms |
| 4 | test growth score none values | ✅ PASSED | 0.1ms |
| 5 | test research returns all required keys | ✅ PASSED | 114.4ms |
| 6 | test disclaimer always present | ✅ PASSED | 129.4ms |
| 7 | test final rating is valid value | ✅ PASSED | 106.6ms |
| 8 | test scores are in range | ✅ PASSED | 107.0ms |
| 9 | test invalid ticker raises | ✅ PASSED | 58.8ms |
| 10 | test growth score high growth | ✅ PASSED | 62.5ms |
| 11 | test growth score low growth | ✅ PASSED | 57.6ms |
| 12 | test rule based synthesis strong candidate | ✅ PASSED | 52.3ms |
| 13 | test llm synthesis with mock | ✅ PASSED | 200.5ms |
| 14 | test llm synthesis falls back on error | ✅ PASSED | 190.2ms |
| 15 | test run single stock | ✅ PASSED | 48.1ms |
| 16 | test run failed stock included as error | ✅ PASSED | 47.0ms |
| 17 | test run multiple stocks | ✅ PASSED | 49.3ms |
| 18 | test report structure | ✅ PASSED | 51.2ms |
| 19 | test top pick structure | ✅ PASSED | 49.5ms |
| 20 | test run produces all category keys | ✅ PASSED | 112.8ms |
| 21 | test run stats populated | ✅ PASSED | 50.6ms |
| 22 | test run handles orchestrator failure | ✅ PASSED | 50.2ms |
| 23 | test run progress callback called | ✅ PASSED | 69.7ms |
| 24 | test run enriches report with earnings data | ✅ PASSED | 49.1ms |
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
| 4 | test rule based synthesis avoid high risk | ✅ PASSED | 49.9ms |
| 5 | test score buffett high risk penalised | ✅ PASSED | 0.1ms |
| 6 | test avoid list excludes strong candidates with low risk | ✅ PASSED | 48.9ms |
| 7 | test missing risk appetite flagged | ✅ PASSED | 0.1ms |
| 8 | test high debt flag detected | ✅ PASSED | 0.2ms |
| 9 | test negative fcf flag detected | ✅ PASSED | 0.1ms |
| 10 | test high promoter pledge flag | ✅ PASSED | 0.2ms |
| 11 | test low promoter holding flag | ✅ PASSED | 0.2ms |
| 12 | test overvalued pe flag | ✅ PASSED | 0.1ms |
| 13 | test auditor change flag | ✅ PASSED | 0.2ms |
| 14 | test governance issue flag | ✅ PASSED | 0.1ms |
| 15 | test sudden price spike flag | ✅ PASSED | 0.1ms |
| 16 | test negative operating cash flow flag | ✅ PASSED | 0.2ms |
| 17 | test clean company no flags | ✅ PASSED | 0.1ms |
| 18 | test de exactly at threshold no flag | ✅ PASSED | 0.2ms |
| 19 | test pe exactly at threshold no flag | ✅ PASSED | 0.1ms |
| 20 | test risk score zero for no flags | ✅ PASSED | 0.1ms |
| 21 | test risk score severe flags higher | ✅ PASSED | 0.1ms |
| 22 | test risk score capped at 10 | ✅ PASSED | 0.1ms |
| 23 | test analyze returns all keys | ✅ PASSED | 0.2ms |
| 24 | test analyze high risk labeled correctly | ✅ PASSED | 0.2ms |
| 25 | test analyze low risk labeled correctly | ✅ PASSED | 0.2ms |
| 26 | test quant score risky stock | ✅ PASSED | 0.1ms |

## ✅ Valuation & DCF (44/44 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test dividend yield zero price returns none | ✅ PASSED | 0.1ms |
| 2 | test dividend yield negative price returns none | ✅ PASSED | 0.2ms |
| 3 | test score pe between 20 and 30 | ✅ PASSED | 0.1ms |
| 4 | test score pe between 30 and 50 | ✅ PASSED | 0.1ms |
| 5 | test score pe none | ✅ PASSED | 0.1ms |
| 6 | test score pb between 1 and 1 5 | ✅ PASSED | 0.1ms |
| 7 | test score pb between 3 and 5 | ✅ PASSED | 0.1ms |
| 8 | test score pb none | ✅ PASSED | 0.1ms |
| 9 | test score peg between 1 and 1 5 | ✅ PASSED | 0.1ms |
| 10 | test score peg between 1 5 and 2 | ✅ PASSED | 0.1ms |
| 11 | test score peg none | ✅ PASSED | 0.1ms |
| 12 | test score margin of safety between 25 and 40 | ✅ PASSED | 0.1ms |
| 13 | test score margin of safety between 10 and 25 | ✅ PASSED | 0.1ms |
| 14 | test score margin of safety between 0 and 10 | ✅ PASSED | 0.1ms |
| 15 | test score margin of safety none intrinsic | ✅ PASSED | 0.1ms |
| 16 | test dcf zero shares uses default 1 | ✅ PASSED | 0.2ms |
| 17 | test score pe between 15 and 20 | ✅ PASSED | 0.1ms |
| 18 | test score pb between 1 5 and 3 | ✅ PASSED | 0.2ms |
| 19 | test score pb at or below 1 | ✅ PASSED | 0.1ms |
| 20 | test pe ratio normal | ✅ PASSED | 0.1ms |
| 21 | test pe ratio negative eps returns none | ✅ PASSED | 0.1ms |
| 22 | test pe ratio zero eps returns none | ✅ PASSED | 0.1ms |
| 23 | test pb ratio normal | ✅ PASSED | 0.1ms |
| 24 | test pb ratio zero book returns none | ✅ PASSED | 0.1ms |
| 25 | test ev ebitda normal | ✅ PASSED | 0.1ms |
| 26 | test ev ebitda zero ebitda returns none | ✅ PASSED | 0.1ms |
| 27 | test peg ratio normal | ✅ PASSED | 0.1ms |
| 28 | test peg ratio zero growth returns none | ✅ PASSED | 0.1ms |
| 29 | test dividend yield normal | ✅ PASSED | 0.1ms |
| 30 | test score pe graham value | ✅ PASSED | 0.1ms |
| 31 | test score pe very low | ✅ PASSED | 0.1ms |
| 32 | test score pe very high | ✅ PASSED | 0.1ms |
| 33 | test score pb graham attractive | ✅ PASSED | 0.1ms |
| 34 | test score pb expensive | ✅ PASSED | 0.1ms |
| 35 | test score peg lynch undervalued | ✅ PASSED | 0.1ms |
| 36 | test score peg overvalued | ✅ PASSED | 0.1ms |
| 37 | test score margin of safety deep value | ✅ PASSED | 0.1ms |
| 38 | test score margin of safety above intrinsic | ✅ PASSED | 0.1ms |
| 39 | test dcf positive fcf | ✅ PASSED | 0.3ms |
| 40 | test dcf negative fcf returns error | ✅ PASSED | 0.1ms |
| 41 | test dcf assumptions shown | ✅ PASSED | 0.2ms |
| 42 | test dcf custom margin of safety | ✅ PASSED | 0.2ms |
| 43 | test analyze returns all keys | ✅ PASSED | 0.3ms |
| 44 | test overall valuation score in range | ✅ PASSED | 0.1ms |
