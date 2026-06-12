# Business Test Case Report
**Generated:** 2026-06-12 14:42 UTC  
**Total:** 76 | **✅ Passed:** 76 | **❌ Failed:** 0 | **⏭ Skipped:** 0

> This is educational research software. All tests validate research and safety logic — not financial advice.

## ✅ Data Collection (3/3 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test analyze with mock data | ✅ PASSED | 10296.1ms |
| 2 | test analyze empty dataframe | ✅ PASSED | 1.2ms |
| 3 | test compute trends insufficient data | ✅ PASSED | 0.1ms |

## ✅ General (63/63 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test unicorn universe not empty | ✅ PASSED | 0.1ms |
| 2 | test unicorn universe no duplicates | ✅ PASSED | 0.1ms |
| 3 | test unicorn universe excludes large caps | ✅ PASSED | 0.1ms |
| 4 | test theme map has all expected themes | ✅ PASSED | 0.1ms |
| 5 | test detect themes defense | ✅ PASSED | 0.2ms |
| 6 | test detect themes solar | ✅ PASSED | 0.1ms |
| 7 | test detect themes multiple | ✅ PASSED | 0.2ms |
| 8 | test detect themes no match | ✅ PASSED | 0.2ms |
| 9 | test detect themes cdmo | ✅ PASSED | 0.1ms |
| 10 | test parse info basic | ✅ PASSED | 0.7ms |
| 11 | test parse info themes detected | ✅ PASSED | 0.2ms |
| 12 | test parse info de none when missing | ✅ PASSED | 0.2ms |
| 13 | test filter passes valid stock | ✅ PASSED | 0.2ms |
| 14 | test filter rejects too small mcap | ✅ PASSED | 0.2ms |
| 15 | test filter rejects large cap | ✅ PASSED | 0.2ms |
| 16 | test filter rejects low growth | ✅ PASSED | 0.2ms |
| 17 | test filter rejects high debt | ✅ PASSED | 0.2ms |
| 18 | test filter passes when growth none | ✅ PASSED | 0.1ms |
| 19 | test filter rejects penny stock | ✅ PASSED | 0.1ms |
| 20 | test unicorn score high growth | ✅ PASSED | 0.2ms |
| 21 | test unicorn score all keys present | ✅ PASSED | 0.1ms |
| 22 | test unicorn score capped at 10 | ✅ PASSED | 0.1ms |
| 23 | test unicorn score zero growth | ✅ PASSED | 0.2ms |
| 24 | test hunt returns expected keys | ✅ PASSED | 3.4ms |
| 25 | test hunt all filtered out | ✅ PASSED | 1.3ms |
| 26 | test hunt fetch failure counted | ✅ PASSED | 1.4ms |
| 27 | test hunt top n respected | ✅ PASSED | 5.0ms |
| 28 | test hunt sorted by composite | ✅ PASSED | 1.7ms |
| 29 | test hunt theme breakdown structure | ✅ PASSED | 1.1ms |
| 30 | test hunt progress callback called | ✅ PASSED | 1.3ms |
| 31 | test hunt uses unicorn universe by default | ✅ PASSED | 10.5ms |
| 32 | test hunt candidates have scores | ✅ PASSED | 1.1ms |
| 33 | test parse info converts units correctly | ✅ PASSED | 0.2ms |
| 34 | test prefilter passes good stock | ✅ PASSED | 0.1ms |
| 35 | test prefilter rejects micro cap | ✅ PASSED | 0.1ms |
| 36 | test prefilter rejects penny stock | ✅ PASSED | 0.1ms |
| 37 | test prefilter rejects no revenue | ✅ PASSED | 0.1ms |
| 38 | test prefilter rejects bad roe | ✅ PASSED | 0.1ms |
| 39 | test prefilter high de financial sector exempt | ✅ PASSED | 0.1ms |
| 40 | test quant score high quality stock | ✅ PASSED | 0.1ms |
| 41 | test screen with mocked fetch | ✅ PASSED | 1.9ms |
| 42 | test screen all fetch failures | ✅ PASSED | 1.7ms |
| 43 | test screen progress callback | ✅ PASSED | 1.2ms |
| 44 | test get symbol list fallback | ✅ PASSED | 98.4ms |
| 45 | test nifty100 fallback not empty | ✅ PASSED | 0.2ms |
| 46 | test parse info missing fields handled | ✅ PASSED | 0.1ms |
| 47 | test candidates sorted by composite score | ✅ PASSED | 0.2ms |
| 48 | test analyze returns error on fetch failure | ✅ PASSED | 0.9ms |
| 49 | test pct change calculation | ✅ PASSED | 0.5ms |
| 50 | test earnings quality score strong growth | ✅ PASSED | 0.1ms |
| 51 | test earnings quality score declining | ✅ PASSED | 0.4ms |
| 52 | test compute trends yoy | ✅ PASSED | 0.1ms |
| 53 | test safe cr returns none on bad df | ✅ PASSED | 0.1ms |
| 54 | test create and get job | ✅ PASSED | 0.1ms |
| 55 | test start job | ✅ PASSED | 0.1ms |
| 56 | test complete job | ✅ PASSED | 0.2ms |
| 57 | test fail job | ✅ PASSED | 0.2ms |
| 58 | test update progress | ✅ PASSED | 0.2ms |
| 59 | test get nonexistent job | ✅ PASSED | 0.1ms |
| 60 | test list jobs returns recent | ✅ PASSED | 0.1ms |
| 61 | test list jobs no result payload | ✅ PASSED | 0.1ms |
| 62 | test thread safety | ✅ PASSED | 6.8ms |
| 63 | test job returns copy not reference | ✅ PASSED | 0.2ms |

## ✅ Research Orchestration (9/9 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test run produces all category keys | ✅ PASSED | 94.6ms |
| 2 | test run stats populated | ✅ PASSED | 76.4ms |
| 3 | test run handles orchestrator failure | ✅ PASSED | 68.0ms |
| 4 | test run progress callback called | ✅ PASSED | 94.9ms |
| 5 | test run enriches report with earnings data | ✅ PASSED | 80.6ms |
| 6 | test lynch scoring | ✅ PASSED | 0.2ms |
| 7 | test lynch high peg scores lower | ✅ PASSED | 0.1ms |
| 8 | test pick top10 returns max 10 | ✅ PASSED | 0.3ms |
| 9 | test pick top10 structure | ✅ PASSED | 0.2ms |

## ✅ Risk Detection (1/1 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test quant score risky stock | ✅ PASSED | 0.1ms |
