"""IPO Data Agent — current, upcoming, and recently-listed IPO details.

Data source: NSE's public IPO endpoints (same "public JSON API, no auth" pattern
already used by DataCollectorAgent.fetch_nse_stock_list). SEBI itself does not expose
a structured public API for IPO listings — issue price band, issue size, DRHP link,
and lead managers are SEBI-mandated disclosures that NSE/BSE surface on the exchange's
own IPO pages, which is what these endpoints mirror. BSE has an equivalent IPO page
but no comparably stable public JSON endpoint, so it's left as a documented gap (see
`bse_note` on each record) rather than a fabricated integration.

NSE's IPO endpoints are undocumented JSON APIs guarded by a browser-session check — a
bare GET without first visiting nseindia.com to pick up session cookies typically
comes back 401/403, or an HTML "please enable JavaScript" challenge page instead of
JSON. This agent warms a session once per instance (and re-warms once on a 401/403,
since NSE's session cookies are short-lived) before calling the API. Every fetch
method reports whether the call actually reached NSE (`status: "ok" | "unavailable"`)
instead of silently collapsing a blocked request into "zero IPOs found" — see
docs/integrations.md.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from src.agents.registry import AgentRegistry
from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.validators import validate_ticker

logger = get_logger(__name__)

NSE_BASE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo",
}

NSE_HOME_URL = "https://www.nseindia.com"
NSE_CURRENT_IPO_URL = "https://www.nseindia.com/api/ipo-current-issue"
NSE_UPCOMING_IPO_URL = "https://www.nseindia.com/api/all-upcoming-issues?category=ipo"
NSE_PAST_IPO_URL = "https://www.nseindia.com/api/public-past-issues"
# Separate "IPO Tracker" / issue-detail endpoint for a single symbol's demand/bid
# (subscription) data — distinct from the listing pages above.
NSE_ISSUE_DETAIL_URL = "https://www.nseindia.com/api/ipo-detail"

BSE_NOTE = (
    "BSE does not publish a comparably stable public JSON IPO endpoint — cross-check "
    "against bseindia.com/publicissue for BSE-only issues."
)
SEBI_NOTE = (
    "Issue price, size, and dates are SEBI-mandated disclosures surfaced via the "
    "exchange's public IPO API — SEBI itself does not expose a structured IPO API."
)


@AgentRegistry.register("ipo_data")
class IPODataAgent:
    """
    Fetches IPO details (mainboard + SME) from NSE's public IPO endpoints:
    - Current (open for subscription)
    - Upcoming (not yet open)
    - Recently listed (past issues, filterable by lookback window)
    - Per-issue demand/bid detail (fetch_issue_detail — not called in bulk, see below)

    Never scrapes restricted pages — public JSON endpoints only, same as
    DataCollectorAgent. Every `fetch_*` method returns a dict with a `status` field
    ("ok" or "unavailable") and an `error` field, so a blocked/failed NSE request is
    never silently indistinguishable from "NSE has no matching IPOs right now".
    """

    def __init__(self, config=None):
        self.cfg = config or get_config()
        self._http = httpx.Client(timeout=15.0, headers=NSE_BASE_HEADERS, follow_redirects=True)
        self._session_warm = False

    # ------------------------------------------------------------------
    # Low-level fetch (session warm-up, retry, status reporting)
    # ------------------------------------------------------------------

    def _warm_session(self):
        """Visits the NSE homepage once to pick up the session cookies its API
        endpoints require. Best-effort — if even this fails, the subsequent API call
        will also fail and get reported as status='unavailable' with the real reason."""
        try:
            self._http.get(NSE_HOME_URL)
            self._session_warm = True
            logger.debug("NSE session warmed")
        except Exception as exc:
            logger.warning("NSE session warm-up failed: %s", exc)

    def _fetch_json(self, url: str) -> Dict[str, Any]:
        """
        Fetches one NSE endpoint. Returns
        {"status": "ok"|"unavailable", "error": str|None, "data": <raw parsed JSON>}.

        On a 401/403 (the usual "no valid session" signature), re-warms the session
        once and retries before giving up — NSE's session cookies expire quickly.
        """
        if not self._session_warm:
            self._warm_session()

        resp = None
        error: Optional[str] = None
        for attempt in range(2):
            try:
                resp = self._http.get(url)
                if resp.status_code in (401, 403) and attempt == 0:
                    logger.debug(
                        "NSE returned %d for %s — re-warming session and retrying once",
                        resp.status_code, url,
                    )
                    self._session_warm = False
                    self._warm_session()
                    resp = None
                    continue
                resp.raise_for_status()
                break
            except httpx.HTTPStatusError as exc:
                error = f"HTTP {exc.response.status_code}"
                resp = None
                break
            except Exception as exc:
                error = f"{type(exc).__name__}: {exc}"
                resp = None
                break

        if resp is None:
            logger.error("NSE IPO fetch FAILED for %s: %s", url, error)
            return {"status": "unavailable", "error": error or "unknown error", "data": None}

        try:
            data = resp.json()
        except Exception as exc:
            logger.error(
                "NSE IPO fetch for %s returned non-JSON (likely a blocked/challenge page): %s",
                url, exc,
            )
            return {"status": "unavailable", "error": f"non-JSON response: {exc}", "data": None}

        logger.info("NSE IPO fetch SUCCESS for %s", url)
        return {"status": "ok", "error": None, "data": data}

    def _fetch_records(self, url: str) -> Dict[str, Any]:
        """List-oriented wrapper over _fetch_json for the list/{"data": [...]} endpoints."""
        fetch = self._fetch_json(url)
        if fetch["status"] != "ok":
            return {"status": fetch["status"], "error": fetch["error"], "records": []}
        data = fetch["data"]
        if isinstance(data, list):
            records = data
        elif isinstance(data, dict):
            records = data.get("data", [])
        else:
            records = []
        logger.info("NSE IPO fetch %s: %d records", url, len(records))
        return {"status": "ok", "error": None, "records": records}

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------

    def _normalize(self, raw: Dict[str, Any], status: str, source_url: str) -> Dict[str, Any]:
        """Maps NSE's IPO record shape (which varies slightly per endpoint) into one
        common schema, defensively — unrecognised/renamed fields just come back None
        rather than raising, matching the resilience style used across this codebase."""
        symbol = raw.get("symbol") or raw.get("series") or raw.get("companySymbol")
        return {
            "symbol": symbol,
            "company_name": raw.get("companyName") or raw.get("name") or symbol,
            "exchange": "NSE",
            "series": raw.get("series") or raw.get("seriesRemarks") or "mainboard",
            "status": status,
            "isin": raw.get("isin") or raw.get("symbolIsin"),
            "issue_price_min": raw.get("issuePriceMin") or raw.get("floorPrice"),
            "issue_price_max": raw.get("issuePriceMax") or raw.get("capPrice"),
            "lot_size": raw.get("marketLot") or raw.get("lotSize"),
            "issue_size_cr": raw.get("issueSize"),
            "open_date": raw.get("issueStartDate") or raw.get("startDate"),
            "close_date": raw.get("issueEndDate") or raw.get("endDate"),
            "listing_date": raw.get("listingDate"),
            "source_url": source_url,
            "sebi_note": SEBI_NOTE,
            "bse_note": BSE_NOTE,
            "fetched_at": datetime.utcnow().isoformat(),
        }

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def fetch_current_ipos(self) -> Dict[str, Any]:
        """IPOs currently open for subscription.

        Returns {"status", "error", "records": [...]}.
        """
        fetch = self._fetch_records(NSE_CURRENT_IPO_URL)
        records = [self._normalize(r, "open", NSE_CURRENT_IPO_URL) for r in fetch["records"]]
        return {**fetch, "records": records}

    def fetch_upcoming_ipos(self) -> Dict[str, Any]:
        """IPOs announced but not yet open for subscription.

        Returns {"status", "error", "records": [...]}.
        """
        fetch = self._fetch_records(NSE_UPCOMING_IPO_URL)
        records = [self._normalize(r, "upcoming", NSE_UPCOMING_IPO_URL) for r in fetch["records"]]
        return {**fetch, "records": records}

    def fetch_recently_listed_ipos(self, months: Optional[int] = None) -> Dict[str, Any]:
        """
        IPOs that have already listed, within the lookback window.

        Args:
            months: how many months back counts as "recently listed". Defaults to
                    config.ipo.lookback_months (config/default.yaml).

        Returns {"status", "error", "records": [...], "total_received": int,
        "total_after_date_filter": int, "lookback_days": int} — the counts let
        callers (e.g. IPOUnicornHunterAgent) report a diagnosis funnel instead of a
        single opaque "0 candidates".
        """
        months = months if months is not None else self.cfg.ipo.lookback_months
        lookback_days = months * 30
        cutoff = datetime.utcnow() - timedelta(days=lookback_days)

        fetch = self._fetch_records(NSE_PAST_IPO_URL)
        if fetch["status"] != "ok":
            return {
                "status": fetch["status"], "error": fetch["error"], "records": [],
                "total_received": 0, "total_after_date_filter": 0, "lookback_days": lookback_days,
            }

        normalized_all = [self._normalize(r, "listed", NSE_PAST_IPO_URL) for r in fetch["records"]]
        total_received = len(normalized_all)

        filtered = []
        for record in normalized_all:
            listing_date = self._parse_date(record.get("listing_date"))
            if listing_date is None or listing_date >= cutoff:
                record["days_since_listing"] = (
                    (datetime.utcnow() - listing_date).days if listing_date else None
                )
                filtered.append(record)

        logger.info(
            "IPO fetch funnel | received=%d | lookback_days=%d | after_date_filter=%d",
            total_received, lookback_days, len(filtered),
        )
        return {
            "status": "ok", "error": None, "records": filtered,
            "total_received": total_received, "total_after_date_filter": len(filtered),
            "lookback_days": lookback_days,
        }

    def fetch_issue_detail(self, symbol: str) -> Dict[str, Any]:
        """
        Per-issue demand/bid (subscription) detail — e.g. overall/QIB/HNI/retail
        subscription multiples — from NSE's separate IPO issue-detail page (NSE's
        "IPO Tracker" is distinct from the current/upcoming/past listing pages above).

        NOT called automatically by IPOUnicornHunterAgent.hunt() — one extra HTTP
        call per candidate would multiply session/rate-limit risk across a whole
        hunt. Use it for a single-symbol deep dive (e.g. a Streamlit detail view).

        Field names here are a best-effort mapping of NSE's issue-detail JSON shape;
        this hasn't been verified against a live response (network access to
        nseindia.com wasn't available while building this — see
        docs/integrations.md). The raw response is included under "raw" so the
        mapping can be corrected once you can confirm the real field names.
        """
        symbol = validate_ticker(symbol)
        fetch = self._fetch_json(f"{NSE_ISSUE_DETAIL_URL}?symbol={symbol}")
        if fetch["status"] != "ok":
            return {"status": fetch["status"], "error": fetch["error"], "symbol": symbol, "subscription": None}

        data = fetch["data"] if isinstance(fetch["data"], dict) else {}
        demand = data.get("demand") or data.get("subscriptionDetails") or {}
        subscription = {
            "overall_times": demand.get("noOfTimesSubscribed") or data.get("overallSubscription"),
            "qib_times": demand.get("qibSubscription") or data.get("qibTimes"),
            "hni_times": demand.get("hniSubscription") or data.get("hniTimes"),
            "retail_times": demand.get("retailSubscription") or data.get("retailTimes"),
        }
        return {"status": "ok", "error": None, "symbol": symbol, "subscription": subscription, "raw": data}

    @staticmethod
    def _parse_date(value: Optional[str]):
        if not value:
            return None
        for fmt in ("%d-%b-%Y", "%d-%b-%y", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        return None

    def close(self):
        self._http.close()
