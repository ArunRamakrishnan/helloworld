# Business Test Case Report
**Generated:** 2026-06-07 07:16 UTC  
**Total:** 44 | **✅ Passed:** 41 | **❌ Failed:** 3 | **⏭ Skipped:** 0

> This is educational research software. All tests validate research and safety logic — not financial advice.

## ✅ Data Collection (3/3 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test analyze with mock data | ✅ PASSED | 9742.1ms |
| 2 | test analyze empty dataframe | ✅ PASSED | 0.7ms |
| 3 | test compute trends insufficient data | ✅ PASSED | 0.1ms |

## ❌ General (28/31 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test parse info converts units correctly | ✅ PASSED | 0.5ms |
| 2 | test prefilter passes good stock — `E   assert False` | ❌ FAILED | 0.2ms |
| 3 | test prefilter rejects micro cap | ✅ PASSED | 0.1ms |
| 4 | test prefilter rejects penny stock | ✅ PASSED | 0.1ms |
| 5 | test prefilter rejects no revenue | ✅ PASSED | 0.1ms |
| 6 | test prefilter rejects bad roe | ✅ PASSED | 0.1ms |
| 7 | test prefilter high de financial sector exempt — `E   assert False` | ❌ FAILED | 0.2ms |
| 8 | test quant score high quality stock | ✅ PASSED | 0.1ms |
| 9 | test screen with mocked fetch — `E    +  where 0 = len([])` | ❌ FAILED | 2.2ms |
| 10 | test screen all fetch failures | ✅ PASSED | 1.2ms |
| 11 | test screen progress callback | ✅ PASSED | 1.0ms |
| 12 | test get symbol list fallback | ✅ PASSED | 62.6ms |
| 13 | test nifty100 fallback not empty | ✅ PASSED | 0.1ms |
| 14 | test parse info missing fields handled | ✅ PASSED | 0.1ms |
| 15 | test candidates sorted by composite score | ✅ PASSED | 0.2ms |
| 16 | test analyze returns error on fetch failure | ✅ PASSED | 0.5ms |
| 17 | test pct change calculation | ✅ PASSED | 0.2ms |
| 18 | test earnings quality score strong growth | ✅ PASSED | 0.1ms |
| 19 | test earnings quality score declining | ✅ PASSED | 0.1ms |
| 20 | test compute trends yoy | ✅ PASSED | 0.1ms |
| 21 | test safe cr returns none on bad df | ✅ PASSED | 0.1ms |
| 22 | test create and get job | ✅ PASSED | 0.1ms |
| 23 | test start job | ✅ PASSED | 0.1ms |
| 24 | test complete job | ✅ PASSED | 0.1ms |
| 25 | test fail job | ✅ PASSED | 0.1ms |
| 26 | test update progress | ✅ PASSED | 0.1ms |
| 27 | test get nonexistent job | ✅ PASSED | 0.1ms |
| 28 | test list jobs returns recent | ✅ PASSED | 0.1ms |
| 29 | test list jobs no result payload | ✅ PASSED | 0.1ms |
| 30 | test thread safety | ✅ PASSED | 6.2ms |
| 31 | test job returns copy not reference | ✅ PASSED | 0.1ms |

## ✅ Research Orchestration (9/9 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test run produces all category keys | ✅ PASSED | 63.8ms |
| 2 | test run stats populated | ✅ PASSED | 51.2ms |
| 3 | test run handles orchestrator failure | ✅ PASSED | 48.9ms |
| 4 | test run progress callback called | ✅ PASSED | 67.1ms |
| 5 | test run enriches report with earnings data | ✅ PASSED | 50.6ms |
| 6 | test lynch scoring | ✅ PASSED | 0.1ms |
| 7 | test lynch high peg scores lower | ✅ PASSED | 0.1ms |
| 8 | test pick top10 returns max 10 | ✅ PASSED | 0.3ms |
| 9 | test pick top10 structure | ✅ PASSED | 0.1ms |

## ✅ Risk Detection (1/1 passed)

| # | Test Case | Status | Duration |
|---|-----------|--------|----------|
| 1 | test quant score risky stock | ✅ PASSED | 0.1ms |

## ❌ Failed Tests — Detail

### tests/test_universe_scan.py::TestUniverseScreenerAgent::test_prefilter_passes_good_stock
```
E   assert False
```

### tests/test_universe_scan.py::TestUniverseScreenerAgent::test_prefilter_high_de_financial_sector_exempt
```
E   assert False
```

### tests/test_universe_scan.py::TestUniverseScreenerAgent::test_screen_with_mocked_fetch
```
E    +  where 0 = len([])
```
