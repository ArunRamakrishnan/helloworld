# Business Test Case Report
**Generated:** 2026-06-07 01:28 UTC  
**Total:** 244 | **✅ Passed:** 244 | **❌ Failed:** 0 | **⏭ Skipped:** 0

> This is educational research software. All tests validate research and safety logic — not financial advice.

## ✅ API Endpoints (17/17 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test health returns ok | ✅ PASSED | 10.0ms |
| 2 | test categories returns six categories | ✅ PASSED | 5.2ms |
| 3 | test categories has disclaimer | ✅ PASSED | 4.6ms |
| 4 | test disclaimer endpoint | ✅ PASSED | 3.9ms |
| 5 | test order preview returns preview | ✅ PASSED | 4.8ms |
| 6 | test order preview shows paper trade mode | ✅ PASSED | 5.0ms |
| 7 | test order place rejected without confirmation | ✅ PASSED | 4.7ms |
| 8 | test order place accepted with confirmation | ✅ PASSED | 4.8ms |
| 9 | test order place rejected insufficient funds | ✅ PASSED | 4.0ms |
| 10 | test order side validation | ✅ PASSED | 2.8ms |
| 11 | test paper log returns list | ✅ PASSED | 4.5ms |
| 12 | test research returns 200 | ✅ PASSED | 61.8ms |
| 13 | test research contains disclaimer | ✅ PASSED | 30.0ms |
| 14 | test research invalid ticker in body returns 400 | ✅ PASSED | 28.2ms |
| 15 | test research scores in range | ✅ PASSED | 30.6ms |
| 16 | test research 500 on unexpected error | ✅ PASSED | 6.8ms |
| 17 | test research 400 on value error | ✅ PASSED | 5.5ms |

## ✅ Audit & Prompt Versioning (8/8 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test returns string | ✅ PASSED | 2.7ms |
| 2 | test returns unknown on failure | ✅ PASSED | 1.5ms |
| 3 | test record change creates prompt file | ✅ PASSED | 3.2ms |
| 4 | test record change content includes reason | ✅ PASSED | 2.7ms |
| 5 | test record change increments version | ✅ PASSED | 5.0ms |
| 6 | test changelog is updated | ✅ PASSED | 2.4ms |
| 7 | test changed files listed in prompt | ✅ PASSED | 2.6ms |
| 8 | test backtest result included when provided | ✅ PASSED | 2.6ms |

## ✅ Broker & Order Execution (18/18 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test valid order request | ✅ PASSED | 0.4ms |
| 2 | test ticker normalised to uppercase | ✅ PASSED | 0.2ms |
| 3 | test invalid ticker raises | ✅ PASSED | 0.4ms |
| 4 | test invalid quantity raises | ✅ PASSED | 0.2ms |
| 5 | test zero quantity raises | ✅ PASSED | 0.2ms |
| 6 | test negative price raises | ✅ PASSED | 0.2ms |
| 7 | test preview contains all fields | ✅ PASSED | 0.2ms |
| 8 | test preview estimated value correct | ✅ PASSED | 0.2ms |
| 9 | test is paper trading by default | ✅ PASSED | 1.3ms |
| 10 | test order rejected without confirmation | ✅ PASSED | 1.2ms |
| 11 | test paper order placed with confirmation | ✅ PASSED | 1.4ms |
| 12 | test insufficient funds rejected | ✅ PASSED | 1.1ms |
| 13 | test paper trade log records order | ✅ PASSED | 2.2ms |
| 14 | test multiple orders in log | ✅ PASSED | 2.0ms |
| 15 | test preview shows paper trade mode | ✅ PASSED | 1.2ms |
| 16 | test cancel paper trade with confirmation | ✅ PASSED | 1.2ms |
| 17 | test cancel without confirmation rejected | ✅ PASSED | 1.0ms |
| 18 | test disclaimer always in preview | ✅ PASSED | 1.2ms |

## ✅ Coverage Gap Tests (2/2 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test get logger returns same instance on repeat call | ✅ PASSED | 0.3ms |
| 2 | test get logger custom level | ✅ PASSED | 1.4ms |

## ✅ Data Collection (8/8 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test fetch historical prices general exception returns empty | ✅ PASSED | 26.2ms |
| 2 | test fetch nse stock list returns list on success | ✅ PASSED | 2.5ms |
| 3 | test fetch nse stock list returns empty on error | ✅ PASSED | 1.0ms |
| 4 | test fetch nse stock list stores source url | ✅ PASSED | 1.8ms |
| 5 | test fetch financials screener returns ticker | ✅ PASSED | 0.4ms |
| 6 | test fetch historical prices no yfinance returns empty | ✅ PASSED | 0.7ms |
| 7 | test close does not raise | ✅ PASSED | 0.2ms |
| 8 | test validate ticker in fetch financials | ✅ PASSED | 0.3ms |

## ✅ Fundamental Analysis (47/47 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test compute roce normal | ✅ PASSED | 0.2ms |
| 2 | test compute roce zero capital employed | ✅ PASSED | 0.2ms |
| 3 | test compute roce negative capital employed | ✅ PASSED | 0.3ms |
| 4 | test score de between 1 and 2 | ✅ PASSED | 0.2ms |
| 5 | test score de between 0 and 1 | ✅ PASSED | 0.2ms |
| 6 | test score de none | ✅ PASSED | 0.1ms |
| 7 | test score fcf zero revenue | ✅ PASSED | 0.2ms |
| 8 | test score fcf medium | ✅ PASSED | 0.2ms |
| 9 | test score fcf low positive | ✅ PASSED | 0.2ms |
| 10 | test score fcf negative | ✅ PASSED | 0.2ms |
| 11 | test score revenue cagr 15pct | ✅ PASSED | 0.2ms |
| 12 | test score revenue cagr 10pct | ✅ PASSED | 0.2ms |
| 13 | test score revenue cagr 5pct | ✅ PASSED | 0.2ms |
| 14 | test score revenue cagr low positive | ✅ PASSED | 0.2ms |
| 15 | test profit cagr negative start returns none | ✅ PASSED | 0.2ms |
| 16 | test revenue cagr insufficient data | ✅ PASSED | 0.2ms |
| 17 | test overall score all none | ✅ PASSED | 0.2ms |
| 18 | test revenue cagr returns value when enough data | ✅ PASSED | 0.2ms |
| 19 | test profit cagr none end value | ✅ PASSED | 0.2ms |
| 20 | test profit cagr valid returns value | ✅ PASSED | 0.2ms |
| 21 | test score roe between 10 and 15 | ✅ PASSED | 0.2ms |
| 22 | test score fcf between 5 and 10 | ✅ PASSED | 0.2ms |
| 23 | test cagr basic | ✅ PASSED | 0.2ms |
| 24 | test cagr zero start returns none | ✅ PASSED | 0.2ms |
| 25 | test cagr negative years returns none | ✅ PASSED | 0.1ms |
| 26 | test cagr none inputs | ✅ PASSED | 0.1ms |
| 27 | test compute roe normal | ✅ PASSED | 0.3ms |
| 28 | test compute roe zero equity | ✅ PASSED | 0.2ms |
| 29 | test compute debt equity normal | ✅ PASSED | 0.2ms |
| 30 | test compute debt equity zero equity | ✅ PASSED | 0.2ms |
| 31 | test compute interest coverage normal | ✅ PASSED | 0.2ms |
| 32 | test compute interest coverage zero interest | ✅ PASSED | 0.2ms |
| 33 | test compute fcf | ✅ PASSED | 0.3ms |
| 34 | test score roe excellent | ✅ PASSED | 0.2ms |
| 35 | test score roe good | ✅ PASSED | 0.2ms |
| 36 | test score roe minimum buffett | ✅ PASSED | 0.1ms |
| 37 | test score roe poor | ✅ PASSED | 0.2ms |
| 38 | test score roe negative | ✅ PASSED | 0.2ms |
| 39 | test score roe none | ✅ PASSED | 0.2ms |
| 40 | test score debt equity no debt | ✅ PASSED | 0.2ms |
| 41 | test score debt equity graham safe | ✅ PASSED | 0.2ms |
| 42 | test score debt equity high risk | ✅ PASSED | 0.2ms |
| 43 | test score revenue cagr high growth | ✅ PASSED | 0.1ms |
| 44 | test score revenue cagr negative | ✅ PASSED | 0.2ms |
| 45 | test analyze with statements | ✅ PASSED | 0.4ms |
| 46 | test analyze empty statements returns error | ✅ PASSED | 0.3ms |
| 47 | test analyze with quarterly only returns none cagr | ✅ PASSED | 0.4ms |

## ✅ Input Validation (27/27 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test validate ratio none returns none | ✅ PASSED | 0.2ms |
| 2 | test validate ratio valid float | ✅ PASSED | 0.2ms |
| 3 | test validate ratio valid int | ✅ PASSED | 0.2ms |
| 4 | test validate ratio non numeric raises | ✅ PASSED | 0.2ms |
| 5 | test validate score non numeric raises | ✅ PASSED | 0.2ms |
| 6 | test validate price non numeric raises | ✅ PASSED | 0.2ms |
| 7 | test validate quantity float truncated | ✅ PASSED | 0.2ms |
| 8 | test validate ratio zero valid | ✅ PASSED | 0.2ms |
| 9 | test valid ticker | ✅ PASSED | 0.2ms |
| 10 | test valid ticker with hyphen | ✅ PASSED | 0.2ms |
| 11 | test empty ticker raises | ✅ PASSED | 0.2ms |
| 12 | test none ticker raises | ✅ PASSED | 0.2ms |
| 13 | test whitespace stripped | ✅ PASSED | 0.2ms |
| 14 | test valid quantity | ✅ PASSED | 0.2ms |
| 15 | test string quantity converted | ✅ PASSED | 0.2ms |
| 16 | test zero raises | ✅ PASSED | 0.3ms |
| 17 | test negative raises | ✅ PASSED | 0.2ms |
| 18 | test non numeric raises | ✅ PASSED | 0.2ms |
| 19 | test valid price | ✅ PASSED | 0.2ms |
| 20 | test string price converted | ✅ PASSED | 0.2ms |
| 21 | test zero price raises | ✅ PASSED | 0.2ms |
| 22 | test negative price raises | ✅ PASSED | 0.3ms |
| 23 | test valid score 10 | ✅ PASSED | 0.2ms |
| 24 | test valid score 0 | ✅ PASSED | 0.2ms |
| 25 | test score above 10 raises | ✅ PASSED | 0.2ms |
| 26 | test score below 0 raises | ✅ PASSED | 0.2ms |
| 27 | test string score converted | ✅ PASSED | 0.2ms |

## ✅ Moat & Business Quality (17/17 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test fallback score returns all dimensions | ✅ PASSED | 1.2ms |
| 2 | test fallback score is 5 for all | ✅ PASSED | 1.0ms |
| 3 | test overall moat score in range | ✅ PASSED | 2.1ms |
| 4 | test overall moat score max inputs gives near 10 | ✅ PASSED | 1.0ms |
| 5 | test overall moat score min inputs gives 0 | ✅ PASSED | 1.0ms |
| 6 | test analyze without llm uses fallback | ✅ PASSED | 1.3ms |
| 7 | test analyze with llm success | ✅ PASSED | 26.8ms |
| 8 | test analyze with llm fallback on error | ✅ PASSED | 27.4ms |
| 9 | test analyze returns ticker | ✅ PASSED | 2.6ms |
| 10 | test analyze empty articles returns neutral | ✅ PASSED | 1.1ms |
| 11 | test keyword fallback positive sentiment | ✅ PASSED | 1.1ms |
| 12 | test keyword fallback negative sentiment | ✅ PASSED | 1.2ms |
| 13 | test keyword fallback mixed sentiment | ✅ PASSED | 1.0ms |
| 14 | test analyze without llm uses keyword fallback | ✅ PASSED | 1.2ms |
| 15 | test analyze with llm success | ✅ PASSED | 26.3ms |
| 16 | test analyze with llm fallback on error | ✅ PASSED | 28.6ms |
| 17 | test format articles caps at 20 | ✅ PASSED | 1.9ms |

## ✅ News & Sentiment (3/3 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test fetch news returns empty when no api key | ✅ PASSED | 27.3ms |
| 2 | test fetch news returns articles on success | ✅ PASSED | 2.0ms |
| 3 | test fetch news returns empty on error | ✅ PASSED | 0.7ms |

## ✅ Portfolio Construction (16/16 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test sector weight clamped when sector nearly full | ✅ PASSED | 0.5ms |
| 2 | test weight zero triggers break | ✅ PASSED | 0.4ms |
| 3 | test portfolio suggest endpoint | ✅ PASSED | 5.6ms |
| 4 | test missing horizon flagged | ✅ PASSED | 0.2ms |
| 5 | test insufficient emergency fund flagged | ✅ PASSED | 0.2ms |
| 6 | test valid profile no issues | ✅ PASSED | 0.2ms |
| 7 | test exactly six months emergency fund accepted | ✅ PASSED | 0.2ms |
| 8 | test suggest allocation returns allocations | ✅ PASSED | 0.4ms |
| 9 | test allocation pct not exceed single stock limit | ✅ PASSED | 0.3ms |
| 10 | test allocation total not exceed 100 | ✅ PASSED | 0.3ms |
| 11 | test same sector concentration limited | ✅ PASSED | 0.4ms |
| 12 | test disclaimer always present | ✅ PASSED | 0.3ms |
| 13 | test incomplete profile returns error | ✅ PASSED | 0.2ms |
| 14 | test no eligible stocks returns message | ✅ PASSED | 0.2ms |
| 15 | test conservative profile lower single stock limit | ✅ PASSED | 0.5ms |
| 16 | test allocation amount matches pct | ✅ PASSED | 0.4ms |

## ✅ Research Orchestration (14/14 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test growth score between 15 and 20 | ✅ PASSED | 0.2ms |
| 2 | test growth score between 10 and 15 | ✅ PASSED | 0.2ms |
| 3 | test growth score between 5 and 10 | ✅ PASSED | 0.2ms |
| 4 | test growth score none values | ✅ PASSED | 0.3ms |
| 5 | test research returns all required keys | ✅ PASSED | 26.7ms |
| 6 | test disclaimer always present | ✅ PASSED | 29.1ms |
| 7 | test final rating is valid value | ✅ PASSED | 26.6ms |
| 8 | test scores are in range | ✅ PASSED | 29.0ms |
| 9 | test invalid ticker raises | ✅ PASSED | 30.2ms |
| 10 | test growth score high growth | ✅ PASSED | 27.3ms |
| 11 | test growth score low growth | ✅ PASSED | 27.2ms |
| 12 | test rule based synthesis strong candidate | ✅ PASSED | 25.8ms |
| 13 | test llm synthesis with mock | ✅ PASSED | 110.0ms |
| 14 | test llm synthesis falls back on error | ✅ PASSED | 100.9ms |

## ✅ Risk Detection (23/23 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test risk score de above 3 | ✅ PASSED | 0.2ms |
| 2 | test risk score de between 2 and 3 | ✅ PASSED | 0.2ms |
| 3 | test risk score de none no extra penalty | ✅ PASSED | 0.2ms |
| 4 | test rule based synthesis avoid high risk | ✅ PASSED | 26.5ms |
| 5 | test missing risk appetite flagged | ✅ PASSED | 0.2ms |
| 6 | test high debt flag detected | ✅ PASSED | 0.3ms |
| 7 | test negative fcf flag detected | ✅ PASSED | 0.3ms |
| 8 | test high promoter pledge flag | ✅ PASSED | 0.3ms |
| 9 | test low promoter holding flag | ✅ PASSED | 0.3ms |
| 10 | test overvalued pe flag | ✅ PASSED | 0.3ms |
| 11 | test auditor change flag | ✅ PASSED | 0.3ms |
| 12 | test governance issue flag | ✅ PASSED | 0.3ms |
| 13 | test sudden price spike flag | ✅ PASSED | 0.3ms |
| 14 | test negative operating cash flow flag | ✅ PASSED | 0.3ms |
| 15 | test clean company no flags | ✅ PASSED | 0.3ms |
| 16 | test de exactly at threshold no flag | ✅ PASSED | 0.3ms |
| 17 | test pe exactly at threshold no flag | ✅ PASSED | 0.3ms |
| 18 | test risk score zero for no flags | ✅ PASSED | 0.2ms |
| 19 | test risk score severe flags higher | ✅ PASSED | 0.2ms |
| 20 | test risk score capped at 10 | ✅ PASSED | 0.2ms |
| 21 | test analyze returns all keys | ✅ PASSED | 0.4ms |
| 22 | test analyze high risk labeled correctly | ✅ PASSED | 0.4ms |
| 23 | test analyze low risk labeled correctly | ✅ PASSED | 0.5ms |

## ✅ Valuation & DCF (44/44 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test dividend yield zero price returns none | ✅ PASSED | 0.2ms |
| 2 | test dividend yield negative price returns none | ✅ PASSED | 0.1ms |
| 3 | test score pe between 20 and 30 | ✅ PASSED | 0.1ms |
| 4 | test score pe between 30 and 50 | ✅ PASSED | 0.2ms |
| 5 | test score pe none | ✅ PASSED | 0.2ms |
| 6 | test score pb between 1 and 1 5 | ✅ PASSED | 0.2ms |
| 7 | test score pb between 3 and 5 | ✅ PASSED | 0.2ms |
| 8 | test score pb none | ✅ PASSED | 0.2ms |
| 9 | test score peg between 1 and 1 5 | ✅ PASSED | 0.1ms |
| 10 | test score peg between 1 5 and 2 | ✅ PASSED | 0.2ms |
| 11 | test score peg none | ✅ PASSED | 0.2ms |
| 12 | test score margin of safety between 25 and 40 | ✅ PASSED | 0.2ms |
| 13 | test score margin of safety between 10 and 25 | ✅ PASSED | 0.2ms |
| 14 | test score margin of safety between 0 and 10 | ✅ PASSED | 0.2ms |
| 15 | test score margin of safety none intrinsic | ✅ PASSED | 0.2ms |
| 16 | test dcf zero shares uses default 1 | ✅ PASSED | 0.5ms |
| 17 | test score pe between 15 and 20 | ✅ PASSED | 0.2ms |
| 18 | test score pb between 1 5 and 3 | ✅ PASSED | 0.2ms |
| 19 | test score pb at or below 1 | ✅ PASSED | 0.2ms |
| 20 | test pe ratio normal | ✅ PASSED | 0.2ms |
| 21 | test pe ratio negative eps returns none | ✅ PASSED | 0.2ms |
| 22 | test pe ratio zero eps returns none | ✅ PASSED | 0.2ms |
| 23 | test pb ratio normal | ✅ PASSED | 0.2ms |
| 24 | test pb ratio zero book returns none | ✅ PASSED | 0.2ms |
| 25 | test ev ebitda normal | ✅ PASSED | 0.2ms |
| 26 | test ev ebitda zero ebitda returns none | ✅ PASSED | 0.2ms |
| 27 | test peg ratio normal | ✅ PASSED | 0.2ms |
| 28 | test peg ratio zero growth returns none | ✅ PASSED | 0.2ms |
| 29 | test dividend yield normal | ✅ PASSED | 0.2ms |
| 30 | test score pe graham value | ✅ PASSED | 0.2ms |
| 31 | test score pe very low | ✅ PASSED | 0.2ms |
| 32 | test score pe very high | ✅ PASSED | 0.1ms |
| 33 | test score pb graham attractive | ✅ PASSED | 0.2ms |
| 34 | test score pb expensive | ✅ PASSED | 0.2ms |
| 35 | test score peg lynch undervalued | ✅ PASSED | 0.2ms |
| 36 | test score peg overvalued | ✅ PASSED | 0.2ms |
| 37 | test score margin of safety deep value | ✅ PASSED | 0.2ms |
| 38 | test score margin of safety above intrinsic | ✅ PASSED | 0.2ms |
| 39 | test dcf positive fcf | ✅ PASSED | 0.4ms |
| 40 | test dcf negative fcf returns error | ✅ PASSED | 0.2ms |
| 41 | test dcf assumptions shown | ✅ PASSED | 0.4ms |
| 42 | test dcf custom margin of safety | ✅ PASSED | 0.4ms |
| 43 | test analyze returns all keys | ✅ PASSED | 0.4ms |
| 44 | test overall valuation score in range | ✅ PASSED | 0.2ms |
