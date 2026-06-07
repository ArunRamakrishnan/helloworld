"""Tests for UnicornHunterAgent."""
import pytest
from unittest.mock import MagicMock, patch

from src.agents.unicorn_hunter import (
    UnicornHunterAgent,
    UNICORN_UNIVERSE,
    THEME_MAP,
    _detect_themes,
    MIN_MARKET_CAP_CR,
    MAX_MARKET_CAP_CR,
    MIN_REVENUE_GROWTH,
    MAX_DEBT_EQUITY,
)


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------

def _make_yf_info(
    market_cap=5_000_000_000,      # 500 Cr
    price=250.0,
    revenue=1_500_000_000,         # 150 Cr
    revenue_growth=0.30,
    debt_to_equity=50.0,           # 0.50 after /100
    roe=0.18,
    op_margin=0.15,
    earn_growth=0.25,
    peg=1.2,
    pb=2.5,
    description="Defense electronics and aerospace systems manufacturer in India.",
    sector="Industrials",
    industry="Aerospace & Defense",
):
    return {
        "marketCap": market_cap,
        "regularMarketPrice": price,
        "totalRevenue": revenue,
        "revenueGrowth": revenue_growth,
        "debtToEquity": debt_to_equity,
        "returnOnEquity": roe,
        "operatingMargins": op_margin,
        "earningsGrowth": earn_growth,
        "pegRatio": peg,
        "priceToBook": pb,
        "longBusinessSummary": description,
        "sector": sector,
        "industry": industry,
        "longName": "Test Corp Ltd",
        "freeCashflow": 200_000_000,
        "totalDebt": 500_000_000,
        "totalCash": 300_000_000,
        "ebitda": 400_000_000,
        "trailingPE": 25.0,
        "trailingEps": 10.0,
        "bookValue": 100.0,
        "dividendYield": None,
        "grossMargins": 0.35,
        "profitMargins": 0.12,
        "currentRatio": 2.0,
        "sharesOutstanding": 10_000_000,
        "fiftyTwoWeekHigh": 300.0,
        "fiftyTwoWeekLow": 180.0,
        "beta": 1.1,
    }


@pytest.fixture
def agent():
    return UnicornHunterAgent()


# -----------------------------------------------------------------------
# UNICORN_UNIVERSE sanity checks
# -----------------------------------------------------------------------

def test_unicorn_universe_not_empty():
    assert len(UNICORN_UNIVERSE) > 100


def test_unicorn_universe_no_duplicates():
    assert len(UNICORN_UNIVERSE) == len(set(UNICORN_UNIVERSE))


def test_unicorn_universe_excludes_large_caps():
    # Core household names should NOT be in the unicorn universe
    for ticker in ("RELIANCE", "TCS", "HDFCBANK", "INFY", "KOTAKBANK"):
        assert ticker not in UNICORN_UNIVERSE, f"{ticker} should not be in UNICORN_UNIVERSE"


def test_theme_map_has_all_expected_themes():
    expected = {
        "defense_aerospace", "electronics_ems", "ev_battery", "renewable_solar",
        "specialty_chem", "ai_data_infra", "digital_fintech", "pharma_cdmo",
    }
    assert expected.issubset(THEME_MAP.keys())


# -----------------------------------------------------------------------
# _detect_themes
# -----------------------------------------------------------------------

def test_detect_themes_defense():
    themes = _detect_themes("manufactures defense radar systems", "Industrials", "Defense")
    assert "defense_aerospace" in themes


def test_detect_themes_solar():
    themes = _detect_themes("solar photovoltaic panel maker", "Energy", "Renewable Energy")
    assert "renewable_solar" in themes


def test_detect_themes_multiple():
    themes = _detect_themes(
        "electric vehicle battery pack manufacturer also does solar charging infrastructure",
        "Auto",
        "Battery",
    )
    assert "ev_battery" in themes
    assert "renewable_solar" in themes


def test_detect_themes_no_match():
    themes = _detect_themes("traditional brick and mortar shoe store", "Consumer", "Footwear")
    # Should not match anything meaningful
    assert "defense_aerospace" not in themes
    assert "ev_battery" not in themes


def test_detect_themes_cdmo():
    themes = _detect_themes(
        "contract manufacturing and active pharmaceutical ingredient production",
        "Pharma",
        "CDMO",
    )
    assert "pharma_cdmo" in themes


# -----------------------------------------------------------------------
# _parse_info
# -----------------------------------------------------------------------

def test_parse_info_basic(agent):
    info = _make_yf_info()
    result = agent._parse_info("TESTCO", info)
    assert result["ticker"] == "TESTCO"
    assert result["market_cap_cr"] == pytest.approx(500.0, rel=0.01)
    assert result["revenue_cr"] == pytest.approx(150.0, rel=0.01)
    assert result["debt_equity"] == pytest.approx(0.50, rel=0.01)
    assert result["exchange"] == "NSE"


def test_parse_info_themes_detected(agent):
    info = _make_yf_info(
        description="manufacturer of defense radar and aerospace components",
        sector="Industrials",
        industry="Defense",
    )
    result = agent._parse_info("DEFCO", info)
    assert "defense_aerospace" in result["emerging_themes"]
    assert result["theme_count"] >= 1


def test_parse_info_de_none_when_missing(agent):
    info = _make_yf_info()
    del info["debtToEquity"]
    result = agent._parse_info("TESTCO", info)
    assert result["debt_equity"] is None


# -----------------------------------------------------------------------
# _passes_unicorn_filter
# -----------------------------------------------------------------------

def test_filter_passes_valid_stock(agent):
    stock = {
        "market_cap_cr": 800.0,
        "current_price": 200.0,
        "revenue_cr": 100.0,
        "revenue_growth_yoy": 0.30,
        "debt_equity": 0.50,
    }
    passes, reason = agent._passes_unicorn_filter(stock)
    assert passes is True
    assert reason == ""


def test_filter_rejects_too_small_mcap(agent):
    stock = {
        "market_cap_cr": 50.0,
        "current_price": 200.0,
        "revenue_cr": 100.0,
        "revenue_growth_yoy": 0.30,
        "debt_equity": 0.50,
    }
    passes, reason = agent._passes_unicorn_filter(stock)
    assert passes is False
    assert "small" in reason.lower() or "mcap" in reason.lower()


def test_filter_rejects_large_cap(agent):
    stock = {
        "market_cap_cr": 50_000.0,    # Way above 15,000 ceiling
        "current_price": 2000.0,
        "revenue_cr": 1000.0,
        "revenue_growth_yoy": 0.30,
        "debt_equity": 0.50,
    }
    passes, reason = agent._passes_unicorn_filter(stock)
    assert passes is False
    assert "large cap" in reason.lower() or "not undiscovered" in reason.lower()


def test_filter_rejects_low_growth(agent):
    stock = {
        "market_cap_cr": 800.0,
        "current_price": 100.0,
        "revenue_cr": 100.0,
        "revenue_growth_yoy": 0.03,   # 3% — below 10% threshold
        "debt_equity": 0.50,
    }
    passes, reason = agent._passes_unicorn_filter(stock)
    assert passes is False
    assert "growth" in reason.lower() or "rev_growth" in reason.lower()


def test_filter_rejects_high_debt(agent):
    stock = {
        "market_cap_cr": 800.0,
        "current_price": 100.0,
        "revenue_cr": 100.0,
        "revenue_growth_yoy": 0.30,
        "debt_equity": 3.5,           # Above 2.0 ceiling
    }
    passes, reason = agent._passes_unicorn_filter(stock)
    assert passes is False
    assert "debt" in reason.lower()


def test_filter_passes_when_growth_none(agent):
    """If revenue_growth_yoy is None, the growth filter is skipped (no data ≠ bad)."""
    stock = {
        "market_cap_cr": 800.0,
        "current_price": 100.0,
        "revenue_cr": 100.0,
        "revenue_growth_yoy": None,
        "debt_equity": 0.50,
    }
    passes, _ = agent._passes_unicorn_filter(stock)
    assert passes is True


def test_filter_rejects_penny_stock(agent):
    stock = {
        "market_cap_cr": 200.0,
        "current_price": 2.5,         # Below MIN_PRICE_INR=5
        "revenue_cr": 100.0,
        "revenue_growth_yoy": 0.30,
        "debt_equity": 0.50,
    }
    passes, reason = agent._passes_unicorn_filter(stock)
    assert passes is False


# -----------------------------------------------------------------------
# _unicorn_score
# -----------------------------------------------------------------------

def test_unicorn_score_high_growth(agent):
    stock = {
        "revenue_growth_yoy": 0.55,
        "earnings_growth_yoy": 0.45,
        "market_cap_cr": 400.0,
        "roe": 0.22,
        "debt_equity": 0.30,
        "operating_margin": 0.18,
        "theme_count": 2,
        "peg_ratio": 0.9,
        "pb_ratio": 2.5,
    }
    scores = agent._unicorn_score(stock)
    assert scores["unicorn_growth_score"] >= 5.0
    assert scores["unicorn_composite"] > 5.0


def test_unicorn_score_all_keys_present(agent):
    stock = {
        "revenue_growth_yoy": 0.20,
        "earnings_growth_yoy": 0.15,
        "market_cap_cr": 1000.0,
        "roe": 0.12,
        "debt_equity": 0.60,
        "operating_margin": 0.10,
        "theme_count": 1,
        "peg_ratio": None,
        "pb_ratio": None,
    }
    scores = agent._unicorn_score(stock)
    for key in ("unicorn_growth_score", "unicorn_size_score", "unicorn_theme_score",
                "unicorn_quality_score", "unicorn_valuation_score", "unicorn_composite"):
        assert key in scores


def test_unicorn_score_capped_at_10(agent):
    stock = {
        "revenue_growth_yoy": 2.0,
        "earnings_growth_yoy": 2.0,
        "market_cap_cr": 100.0,
        "roe": 0.50,
        "debt_equity": 0.10,
        "operating_margin": 0.40,
        "theme_count": 10,
        "peg_ratio": 0.3,
        "pb_ratio": 1.0,
    }
    scores = agent._unicorn_score(stock)
    assert scores["unicorn_growth_score"] <= 10.0
    assert scores["unicorn_theme_score"] <= 10.0
    assert scores["unicorn_quality_score"] <= 10.0
    assert scores["unicorn_composite"] <= 10.0


def test_unicorn_score_zero_growth(agent):
    stock = {
        "revenue_growth_yoy": 0,
        "earnings_growth_yoy": 0,
        "market_cap_cr": 5000.0,
        "roe": 0,
        "debt_equity": 0,
        "operating_margin": 0,
        "theme_count": 0,
        "peg_ratio": None,
        "pb_ratio": None,
    }
    scores = agent._unicorn_score(stock)
    assert scores["unicorn_growth_score"] == 0.0
    assert scores["unicorn_composite"] >= 0.0


# -----------------------------------------------------------------------
# hunt() integration (mocked yfinance)
# -----------------------------------------------------------------------

def _make_stock_with_scores(ticker="MTAR", mcap=800.0, rev_growth=0.35):
    return {
        "ticker": ticker,
        "name": ticker,
        "sector": "Industrials",
        "industry": "Aerospace",
        "current_price": 200.0,
        "market_cap_cr": mcap,
        "revenue_cr": 150.0,
        "revenue_growth_yoy": rev_growth,
        "earnings_growth_yoy": 0.30,
        "debt_equity": 0.40,
        "roe": 0.18,
        "operating_margin": 0.15,
        "theme_count": 2,
        "emerging_themes": ["defense_aerospace", "electronics_ems"],
        "peg_ratio": 1.2,
        "pb_ratio": 2.5,
        "fcf_cr": 20.0,
        "debt_cr": 50.0,
        "cash_cr": 30.0,
        "ebitda_cr": 40.0,
        "shares_outstanding_cr": 0.01,
        "eps": 8.0,
        "book_value_per_share": 80.0,
        "dividend_yield": None,
        "gross_margin": 0.35,
        "profit_margin": 0.12,
        "beta": 1.1,
        "52w_high": 280.0,
        "52w_low": 140.0,
        "business_description": "Defense electronics manufacturer",
        "exchange": "NSE",
    }


def test_hunt_returns_expected_keys(agent):
    info = _make_yf_info()
    with patch.object(agent, "_fetch_stock_info", return_value=info):
        result = agent.hunt(symbol_list=["MTAR", "CENTUM"], top_n=10)

    assert "candidates" in result
    assert "theme_breakdown" in result
    assert "total_scanned" in result
    assert "hunt_note" in result
    assert result["total_scanned"] == 2


def test_hunt_all_filtered_out(agent):
    """When all stocks fail the filter, candidates list is empty."""
    bad_info = _make_yf_info(market_cap=5_000_000_000_000)  # 500,000 Cr — way over ceiling
    with patch.object(agent, "_fetch_stock_info", return_value=bad_info):
        result = agent.hunt(symbol_list=["RELIANCE"], top_n=10)

    assert result["candidates"] == []
    assert result["passed_filter"] == 0


def test_hunt_fetch_failure_counted(agent):
    with patch.object(agent, "_fetch_stock_info", return_value=None):
        result = agent.hunt(symbol_list=["BADINPUT"], top_n=10)

    assert result["fetch_failures"] == 1
    assert result["candidates"] == []


def test_hunt_top_n_respected(agent):
    info = _make_yf_info()
    with patch.object(agent, "_fetch_stock_info", return_value=info):
        symbols = [f"SYM{i}" for i in range(20)]
        result = agent.hunt(symbol_list=symbols, top_n=5)

    assert len(result["candidates"]) <= 5


def test_hunt_sorted_by_composite(agent):
    info = _make_yf_info()
    with patch.object(agent, "_fetch_stock_info", return_value=info):
        result = agent.hunt(symbol_list=["A", "B", "C"], top_n=10)

    candidates = result["candidates"]
    if len(candidates) > 1:
        scores = [c["unicorn_composite"] for c in candidates]
        assert scores == sorted(scores, reverse=True)


def test_hunt_theme_breakdown_structure(agent):
    info = _make_yf_info(
        description="defense aerospace systems",
        sector="Industrials",
        industry="Defense",
    )
    with patch.object(agent, "_fetch_stock_info", return_value=info):
        result = agent.hunt(symbol_list=["MTAR"], top_n=10)

    breakdown = result["theme_breakdown"]
    assert isinstance(breakdown, dict)
    for k, v in breakdown.items():
        assert isinstance(k, str)
        assert isinstance(v, list)


def test_hunt_progress_callback_called(agent):
    info = _make_yf_info()
    calls = []
    with patch.object(agent, "_fetch_stock_info", return_value=info):
        agent.hunt(symbol_list=["A", "B"], top_n=10, progress_callback=lambda d, t: calls.append((d, t)))

    assert len(calls) == 2
    assert all(total == 2 for _, total in calls)


def test_hunt_uses_unicorn_universe_by_default(agent):
    with patch.object(agent, "_fetch_stock_info", return_value=None) as mock_fetch:
        agent.hunt(top_n=5)

    # Should have been called once per symbol in UNICORN_UNIVERSE
    assert mock_fetch.call_count == len(UNICORN_UNIVERSE)


def test_hunt_candidates_have_scores(agent):
    info = _make_yf_info()
    with patch.object(agent, "_fetch_stock_info", return_value=info):
        result = agent.hunt(symbol_list=["MTAR"], top_n=5)

    if result["candidates"]:
        c = result["candidates"][0]
        assert "unicorn_composite" in c
        assert "unicorn_growth_score" in c
        assert "emerging_themes" in c
