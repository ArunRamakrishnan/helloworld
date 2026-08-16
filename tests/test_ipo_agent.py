"""Unit tests for IPODataAgent and IPOUnicornHunterAgent."""
from datetime import datetime, timedelta

import pytest
from unittest.mock import MagicMock

from src.agents.ipo_agent import IPODataAgent
from src.agents.ipo_unicorn_hunter import IPOUnicornHunterAgent


def _mock_response(payload):
    resp = MagicMock()
    resp.raise_for_status = MagicMock()
    resp.json.return_value = payload
    return resp


# ------------------------------------------------------------------
# IPODataAgent
# ------------------------------------------------------------------

class TestIPODataAgent:
    def setup_method(self):
        self.agent = IPODataAgent()

    def test_fetch_current_ipos_normalizes_fields(self):
        self.agent._http.get = MagicMock(return_value=_mock_response({
            "data": [{
                "symbol": "FOO", "companyName": "Foo Ltd", "series": "EQ",
                "issuePriceMin": 90, "issuePriceMax": 100,
                "issueStartDate": "01-Jan-2026", "issueEndDate": "03-Jan-2026",
                "isin": "INE000A00000",
            }]
        }))
        result = self.agent.fetch_current_ipos()
        assert len(result) == 1
        rec = result[0]
        assert rec["symbol"] == "FOO"
        assert rec["company_name"] == "Foo Ltd"
        assert rec["status"] == "open"
        assert rec["issue_price_min"] == 90
        assert rec["issue_price_max"] == 100
        assert rec["exchange"] == "NSE"
        assert "sebi_note" in rec
        assert "bse_note" in rec

    def test_fetch_current_ipos_returns_empty_on_error(self):
        self.agent._http.get = MagicMock(side_effect=Exception("network error"))
        assert self.agent.fetch_current_ipos() == []

    def test_fetch_current_ipos_handles_bare_list_response(self):
        self.agent._http.get = MagicMock(return_value=_mock_response(
            [{"symbol": "BAR", "companyName": "Bar Ltd"}]
        ))
        result = self.agent.fetch_current_ipos()
        assert len(result) == 1
        assert result[0]["symbol"] == "BAR"

    def test_fetch_upcoming_ipos_marks_status_upcoming(self):
        self.agent._http.get = MagicMock(return_value=_mock_response({
            "data": [{"symbol": "BAZ", "companyName": "Baz Ltd"}]
        }))
        result = self.agent.fetch_upcoming_ipos()
        assert result[0]["status"] == "upcoming"

    def test_fetch_recently_listed_ipos_filters_by_lookback_window(self):
        recent_date = (datetime.utcnow() - timedelta(days=30)).strftime("%d-%b-%Y")
        stale_date = (datetime.utcnow() - timedelta(days=400)).strftime("%d-%b-%Y")
        self.agent._http.get = MagicMock(return_value=_mock_response({
            "data": [
                {"symbol": "RECENT", "companyName": "Recent Ltd", "listingDate": recent_date},
                {"symbol": "STALE", "companyName": "Stale Ltd", "listingDate": stale_date},
            ]
        }))
        result = self.agent.fetch_recently_listed_ipos(months=12)
        symbols = [r["symbol"] for r in result]
        assert "RECENT" in symbols
        assert "STALE" not in symbols

    def test_fetch_recently_listed_ipos_computes_days_since_listing(self):
        listed = (datetime.utcnow() - timedelta(days=15)).strftime("%d-%b-%Y")
        self.agent._http.get = MagicMock(return_value=_mock_response({
            "data": [{"symbol": "FRESH", "companyName": "Fresh Ltd", "listingDate": listed}]
        }))
        result = self.agent.fetch_recently_listed_ipos(months=12)
        assert result[0]["days_since_listing"] == pytest.approx(15, abs=1)

    def test_fetch_recently_listed_ipos_uses_config_default_months(self):
        self.agent._http.get = MagicMock(return_value=_mock_response({"data": []}))
        # Should not raise even with no explicit months arg.
        result = self.agent.fetch_recently_listed_ipos()
        assert result == []

    def test_fetch_recently_listed_ipos_keeps_records_with_unparseable_date(self):
        self.agent._http.get = MagicMock(return_value=_mock_response({
            "data": [{"symbol": "NODATE", "companyName": "No Date Ltd", "listingDate": "not-a-date"}]
        }))
        result = self.agent.fetch_recently_listed_ipos(months=12)
        assert len(result) == 1
        assert result[0]["days_since_listing"] is None

    @pytest.mark.parametrize("raw,expected", [
        ("01-Jan-2026", datetime(2026, 1, 1)),
        ("2026-01-01", datetime(2026, 1, 1)),
        ("01/01/2026", datetime(2026, 1, 1)),
        ("garbage", None),
        (None, None),
    ])
    def test_parse_date_handles_multiple_formats(self, raw, expected):
        assert IPODataAgent._parse_date(raw) == expected

    def test_close_does_not_raise(self):
        self.agent.close()


# ------------------------------------------------------------------
# IPOUnicornHunterAgent
# ------------------------------------------------------------------

class TestIPOUnicornHunterAgent:
    def setup_method(self):
        self.hunter = IPOUnicornHunterAgent()

    def test_hunt_returns_empty_result_when_no_ipos_found(self):
        self.hunter.ipo_agent.fetch_recently_listed_ipos = MagicMock(return_value=[])
        result = self.hunter.hunt()
        assert result["candidates"] == []
        assert result["total_scanned"] == 0
        assert "hunt_note" in result

    def test_hunt_delegates_to_unicorn_hunter_and_merges_ipo_metadata(self):
        self.hunter.ipo_agent.fetch_recently_listed_ipos = MagicMock(return_value=[
            {"symbol": "FRESH", "listing_date": "01-Jan-2026", "issue_price_min": 90,
             "issue_price_max": 100, "days_since_listing": 10},
        ])
        self.hunter.unicorn_hunter.hunt = MagicMock(return_value={
            "total_scanned": 1, "passed_filter": 1, "fetch_failures": 0, "filtered_out": 0,
            "candidates": [{"ticker": "FRESH", "current_price": 150, "unicorn_composite": 6.0}],
            "candidates_returned": 1, "theme_breakdown": {},
        })
        result = self.hunter.hunt(top_n=10)
        candidate = result["candidates"][0]
        assert candidate["ipo_listing_date"] == "01-Jan-2026"
        assert candidate["days_since_listing"] == 10
        assert candidate["ipo_recency_bonus"] == 2.0   # <=30 days tier
        assert candidate["unicorn_composite"] == pytest.approx(8.0)
        assert candidate["listing_gain_pct"] == pytest.approx(50.0)  # (150-100)/100 * 100

    def test_hunt_reranks_by_composite_after_recency_bonus(self):
        self.hunter.ipo_agent.fetch_recently_listed_ipos = MagicMock(return_value=[
            {"symbol": "OLDER", "listing_date": "01-Jun-2025", "days_since_listing": 300},
            {"symbol": "NEWER", "listing_date": "01-Jul-2026", "days_since_listing": 10},
        ])
        self.hunter.unicorn_hunter.hunt = MagicMock(return_value={
            "total_scanned": 2, "passed_filter": 2, "fetch_failures": 0, "filtered_out": 0,
            "candidates": [
                {"ticker": "OLDER", "unicorn_composite": 7.0},
                {"ticker": "NEWER", "unicorn_composite": 6.0},
            ],
            "candidates_returned": 2, "theme_breakdown": {},
        })
        result = self.hunter.hunt(top_n=10)
        tickers = [c["ticker"] for c in result["candidates"]]
        # NEWER gets +2.0 (6.0->8.0), OLDER gets +0.5 (7.0->7.5) — NEWER should rank first.
        assert tickers[0] == "NEWER"

    def test_hunt_respects_top_n_truncation(self):
        self.hunter.ipo_agent.fetch_recently_listed_ipos = MagicMock(return_value=[
            {"symbol": f"SYM{i}", "days_since_listing": 5} for i in range(5)
        ])
        self.hunter.unicorn_hunter.hunt = MagicMock(return_value={
            "total_scanned": 5, "passed_filter": 5, "fetch_failures": 0, "filtered_out": 0,
            "candidates": [{"ticker": f"SYM{i}", "unicorn_composite": float(i)} for i in range(5)],
            "candidates_returned": 5, "theme_breakdown": {},
        })
        result = self.hunter.hunt(top_n=2)
        assert result["candidates_returned"] == 2
        assert len(result["candidates"]) == 2

    def test_hunt_uses_explicit_symbol_list_without_fetching_ipos(self):
        self.hunter.ipo_agent.fetch_recently_listed_ipos = MagicMock()
        self.hunter.unicorn_hunter.hunt = MagicMock(return_value={
            "total_scanned": 1, "passed_filter": 1, "fetch_failures": 0, "filtered_out": 0,
            "candidates": [{"ticker": "CUSTOM", "unicorn_composite": 5.0}],
            "candidates_returned": 1, "theme_breakdown": {},
        })
        result = self.hunter.hunt(symbol_list=["CUSTOM"], top_n=10)
        self.hunter.ipo_agent.fetch_recently_listed_ipos.assert_not_called()
        assert result["candidates"][0]["ticker"] == "CUSTOM"
        # No IPO metadata available for a raw symbol_list — recency bonus stays 0.
        assert result["candidates"][0]["ipo_recency_bonus"] == 0.0

    def test_close_does_not_raise(self):
        self.hunter.close()
