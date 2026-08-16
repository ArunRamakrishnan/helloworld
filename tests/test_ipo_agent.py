"""Unit tests for IPODataAgent and IPOUnicornHunterAgent."""
from datetime import datetime, timedelta

import pytest
from unittest.mock import MagicMock

from src.agents.ipo_agent import IPODataAgent
from src.agents.ipo_unicorn_hunter import IPOUnicornHunterAgent


def _mock_response(payload, status_code=200):
    resp = MagicMock()
    resp.status_code = status_code
    if status_code >= 400:
        import httpx
        resp.raise_for_status = MagicMock(
            side_effect=httpx.HTTPStatusError("error", request=MagicMock(), response=resp)
        )
    else:
        resp.raise_for_status = MagicMock()
    resp.json.return_value = payload
    return resp


def _warmed_agent() -> IPODataAgent:
    """An IPODataAgent with session warm-up pre-mocked out (so tests don't depend on
    real network access to nseindia.com)."""
    agent = IPODataAgent()
    agent._warm_session = MagicMock(side_effect=lambda: setattr(agent, "_session_warm", True))
    agent._session_warm = True
    return agent


# ------------------------------------------------------------------
# IPODataAgent — low-level fetch / status handling
# ------------------------------------------------------------------

class TestIPODataAgentFetchStatus:
    def setup_method(self):
        self.agent = _warmed_agent()

    def test_fetch_current_ipos_returns_ok_status_on_success(self):
        self.agent._http.get = MagicMock(return_value=_mock_response({
            "data": [{"symbol": "FOO", "companyName": "Foo Ltd", "issuePriceMin": 90, "issuePriceMax": 100}]
        }))
        result = self.agent.fetch_current_ipos()
        assert result["status"] == "ok"
        assert result["error"] is None
        assert len(result["records"]) == 1
        assert result["records"][0]["symbol"] == "FOO"

    def test_fetch_returns_unavailable_status_on_network_error(self):
        self.agent._http.get = MagicMock(side_effect=Exception("connection refused"))
        result = self.agent.fetch_current_ipos()
        assert result["status"] == "unavailable"
        assert "connection refused" in result["error"]
        assert result["records"] == []

    def test_fetch_returns_unavailable_on_persistent_403(self):
        # Both attempts (initial + retry-after-rewarm) come back 403.
        self.agent._http.get = MagicMock(return_value=_mock_response({}, status_code=403))
        result = self.agent.fetch_current_ipos()
        assert result["status"] == "unavailable"
        assert "403" in result["error"]
        # Session should have been re-warmed once after the first 403.
        assert self.agent._warm_session.call_count >= 1

    def test_fetch_retries_once_after_403_then_succeeds(self):
        responses = [_mock_response({}, status_code=403), _mock_response({"data": []})]
        self.agent._http.get = MagicMock(side_effect=responses)
        result = self.agent.fetch_current_ipos()
        assert result["status"] == "ok"
        assert self.agent._http.get.call_count == 2

    def test_fetch_returns_unavailable_on_non_json_response(self):
        resp = MagicMock()
        resp.status_code = 200
        resp.raise_for_status = MagicMock()
        resp.json.side_effect = ValueError("not JSON — got HTML challenge page")
        self.agent._http.get = MagicMock(return_value=resp)
        result = self.agent.fetch_current_ipos()
        assert result["status"] == "unavailable"
        assert "non-JSON" in result["error"]

    def test_warm_session_called_lazily_before_first_request(self):
        agent = IPODataAgent()
        agent._warm_session = MagicMock(side_effect=lambda: setattr(agent, "_session_warm", True))
        agent._http.get = MagicMock(return_value=_mock_response({"data": []}))
        assert agent._session_warm is False
        agent.fetch_current_ipos()
        agent._warm_session.assert_called_once()

    def test_handles_bare_list_response(self):
        self.agent._http.get = MagicMock(return_value=_mock_response(
            [{"symbol": "BAR", "companyName": "Bar Ltd"}]
        ))
        result = self.agent.fetch_current_ipos()
        assert result["status"] == "ok"
        assert result["records"][0]["symbol"] == "BAR"

    def test_upcoming_ipos_marks_status_upcoming(self):
        self.agent._http.get = MagicMock(return_value=_mock_response({
            "data": [{"symbol": "BAZ", "companyName": "Baz Ltd"}]
        }))
        result = self.agent.fetch_upcoming_ipos()
        assert result["records"][0]["status"] == "upcoming"

    def test_normalized_record_carries_sebi_and_bse_notes(self):
        self.agent._http.get = MagicMock(return_value=_mock_response({
            "data": [{"symbol": "FOO", "companyName": "Foo Ltd"}]
        }))
        result = self.agent.fetch_current_ipos()
        assert "sebi_note" in result["records"][0]
        assert "bse_note" in result["records"][0]

    def test_close_does_not_raise(self):
        self.agent.close()


# ------------------------------------------------------------------
# IPODataAgent.fetch_recently_listed_ipos — date filtering + funnel counts
# ------------------------------------------------------------------

class TestFetchRecentlyListedIpos:
    def setup_method(self):
        self.agent = _warmed_agent()

    def test_filters_by_lookback_window_and_reports_funnel_counts(self):
        recent_date = (datetime.utcnow() - timedelta(days=30)).strftime("%d-%b-%Y")
        stale_date = (datetime.utcnow() - timedelta(days=800)).strftime("%d-%b-%Y")
        self.agent._http.get = MagicMock(return_value=_mock_response({
            "data": [
                {"symbol": "RECENT", "companyName": "Recent Ltd", "listingDate": recent_date},
                {"symbol": "STALE", "companyName": "Stale Ltd", "listingDate": stale_date},
            ]
        }))
        result = self.agent.fetch_recently_listed_ipos(months=24)
        symbols = [r["symbol"] for r in result["records"]]
        assert "RECENT" in symbols
        assert "STALE" not in symbols
        assert result["total_received"] == 2
        assert result["total_after_date_filter"] == 1
        assert result["lookback_days"] == 24 * 30

    def test_computes_days_since_listing(self):
        listed = (datetime.utcnow() - timedelta(days=15)).strftime("%d-%b-%Y")
        self.agent._http.get = MagicMock(return_value=_mock_response({
            "data": [{"symbol": "FRESH", "companyName": "Fresh Ltd", "listingDate": listed}]
        }))
        result = self.agent.fetch_recently_listed_ipos(months=24)
        assert result["records"][0]["days_since_listing"] == pytest.approx(15, abs=1)

    def test_uses_config_default_months_when_not_specified(self):
        self.agent._http.get = MagicMock(return_value=_mock_response({"data": []}))
        result = self.agent.fetch_recently_listed_ipos()
        assert result["status"] == "ok"
        assert result["lookback_days"] == self.agent.cfg.ipo.lookback_months * 30

    def test_keeps_records_with_unparseable_date(self):
        self.agent._http.get = MagicMock(return_value=_mock_response({
            "data": [{"symbol": "NODATE", "companyName": "No Date Ltd", "listingDate": "not-a-date"}]
        }))
        result = self.agent.fetch_recently_listed_ipos(months=12)
        assert len(result["records"]) == 1
        assert result["records"][0]["days_since_listing"] is None

    def test_propagates_unavailable_status_with_zeroed_funnel(self):
        self.agent._http.get = MagicMock(side_effect=Exception("timeout"))
        result = self.agent.fetch_recently_listed_ipos(months=12)
        assert result["status"] == "unavailable"
        assert result["records"] == []
        assert result["total_received"] == 0
        assert result["total_after_date_filter"] == 0

    @pytest.mark.parametrize("raw,expected", [
        ("01-Jan-2026", datetime(2026, 1, 1)),
        ("2026-01-01", datetime(2026, 1, 1)),
        ("01/01/2026", datetime(2026, 1, 1)),
        ("garbage", None),
        (None, None),
    ])
    def test_parse_date_handles_multiple_formats(self, raw, expected):
        assert IPODataAgent._parse_date(raw) == expected


# ------------------------------------------------------------------
# IPODataAgent.fetch_issue_detail
# ------------------------------------------------------------------

class TestFetchIssueDetail:
    def setup_method(self):
        self.agent = _warmed_agent()

    def test_returns_subscription_data_on_success(self):
        self.agent._http.get = MagicMock(return_value=_mock_response({
            "demand": {"noOfTimesSubscribed": 45.2, "qibSubscription": 80.1,
                       "hniSubscription": 120.5, "retailSubscription": 10.3},
        }))
        result = self.agent.fetch_issue_detail("foo")
        assert result["status"] == "ok"
        assert result["symbol"] == "FOO"
        assert result["subscription"]["overall_times"] == 45.2
        assert "raw" in result

    def test_returns_unavailable_status_on_failure(self):
        self.agent._http.get = MagicMock(side_effect=Exception("blocked"))
        result = self.agent.fetch_issue_detail("FOO")
        assert result["status"] == "unavailable"
        assert result["subscription"] is None

    def test_validates_ticker(self):
        with pytest.raises(ValueError):
            self.agent.fetch_issue_detail("")


# ------------------------------------------------------------------
# IPOUnicornHunterAgent
# ------------------------------------------------------------------

class TestIPOUnicornHunterAgent:
    def setup_method(self):
        self.hunter = IPOUnicornHunterAgent()

    def test_hunt_returns_data_unavailable_when_nse_fetch_fails(self):
        self.hunter.ipo_agent.fetch_recently_listed_ipos = MagicMock(return_value={
            "status": "unavailable", "error": "HTTP 403", "records": [],
            "total_received": 0, "total_after_date_filter": 0, "lookback_days": 720,
        })
        result = self.hunter.hunt()
        assert result["status"] == "data_unavailable"
        assert "403" in result["hunt_note"]
        assert result["funnel"]["nse_fetch"] == "unavailable"
        assert result["candidates"] == []

    def test_hunt_returns_no_ipos_in_window_when_fetch_ok_but_empty(self):
        self.hunter.ipo_agent.fetch_recently_listed_ipos = MagicMock(return_value={
            "status": "ok", "error": None, "records": [],
            "total_received": 0, "total_after_date_filter": 0, "lookback_days": 720,
        })
        result = self.hunter.hunt()
        assert result["status"] == "no_ipos_in_window"
        assert "no IPOs were listed" in result["hunt_note"]
        assert result["funnel"]["nse_fetch"] == "ok"

    def test_hunt_returns_no_candidates_when_ipos_found_but_none_score(self):
        self.hunter.ipo_agent.fetch_recently_listed_ipos = MagicMock(return_value={
            "status": "ok", "error": None,
            "records": [{"symbol": "FOO", "listing_date": "01-Jan-2026", "days_since_listing": 10}],
            "total_received": 1, "total_after_date_filter": 1, "lookback_days": 720,
        })
        self.hunter.unicorn_hunter.hunt = MagicMock(return_value={
            "total_scanned": 1, "passed_filter": 0, "fetch_failures": 1, "filtered_out": 0,
            "candidates": [], "candidates_returned": 0, "theme_breakdown": {},
        })
        result = self.hunter.hunt()
        assert result["status"] == "no_candidates"
        assert "none matched unicorn criteria" in result["hunt_note"]
        assert result["funnel"]["unicorn_candidates"] == 0

    def test_hunt_ok_delegates_to_unicorn_hunter_and_merges_ipo_metadata(self):
        self.hunter.ipo_agent.fetch_recently_listed_ipos = MagicMock(return_value={
            "status": "ok", "error": None,
            "records": [{"symbol": "FRESH", "listing_date": "01-Jan-2026", "issue_price_min": 90,
                         "issue_price_max": 100, "days_since_listing": 10}],
            "total_received": 1, "total_after_date_filter": 1, "lookback_days": 720,
        })
        self.hunter.unicorn_hunter.hunt = MagicMock(return_value={
            "total_scanned": 1, "passed_filter": 1, "fetch_failures": 0, "filtered_out": 0,
            "candidates": [{"ticker": "FRESH", "current_price": 150, "unicorn_composite": 6.0}],
            "candidates_returned": 1, "theme_breakdown": {},
        })
        result = self.hunter.hunt(top_n=10)
        assert result["status"] == "ok"
        candidate = result["candidates"][0]
        assert candidate["ipo_listing_date"] == "01-Jan-2026"
        assert candidate["days_since_listing"] == 10
        assert candidate["ipo_recency_bonus"] == 2.0   # <=30 days tier
        assert candidate["unicorn_composite"] == pytest.approx(8.0)
        assert candidate["listing_gain_pct"] == pytest.approx(50.0)  # (150-100)/100 * 100
        assert result["funnel"]["unicorn_candidates"] == 1

    def test_hunt_reranks_by_composite_after_recency_bonus(self):
        self.hunter.ipo_agent.fetch_recently_listed_ipos = MagicMock(return_value={
            "status": "ok", "error": None,
            "records": [
                {"symbol": "OLDER", "listing_date": "01-Jun-2025", "days_since_listing": 300},
                {"symbol": "NEWER", "listing_date": "01-Jul-2026", "days_since_listing": 10},
            ],
            "total_received": 2, "total_after_date_filter": 2, "lookback_days": 720,
        })
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
        self.hunter.ipo_agent.fetch_recently_listed_ipos = MagicMock(return_value={
            "status": "ok", "error": None,
            "records": [{"symbol": f"SYM{i}", "days_since_listing": 5} for i in range(5)],
            "total_received": 5, "total_after_date_filter": 5, "lookback_days": 720,
        })
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
        assert result["funnel"]["nse_fetch"] == "skipped (explicit symbol_list)"

    def test_close_does_not_raise(self):
        self.hunter.close()
