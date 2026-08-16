"""IPO Data Agent — current, upcoming, and recently-listed IPO details.

Data source: NSE's public IPO endpoints (same "public JSON API, no auth" pattern
already used by DataCollectorAgent.fetch_nse_stock_list). SEBI itself does not expose
a structured public API for IPO listings — issue price band, issue size, DRHP link,
and lead managers are SEBI-mandated disclosures that NSE/BSE surface on the exchange's
own IPO pages, which is what these endpoints mirror. BSE has an equivalent IPO page
but no comparably stable public JSON endpoint, so it's left as a documented gap (see
`bse_note` on each record) rather than a fabricated integration — same "fail soft,
say so" philosophy as the rest of this codebase's data sources.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import httpx

from src.agents.registry import AgentRegistry
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

NSE_HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/json"}

NSE_CURRENT_IPO_URL = "https://www.nseindia.com/api/ipo-current-issue"
NSE_UPCOMING_IPO_URL = "https://www.nseindia.com/api/all-upcoming-issues?category=ipo"
NSE_PAST_IPO_URL = "https://www.nseindia.com/api/public-past-issues"

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

    Never scrapes restricted pages — public JSON endpoints only, same as
    DataCollectorAgent. Returns an empty list on any fetch/parse failure so callers
    (e.g. IPOUnicornHunterAgent) can degrade gracefully instead of erroring.
    """

    def __init__(self, config=None):
        self.cfg = config or get_config()
        self._http = httpx.Client(timeout=15.0)

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

    def _get(self, url: str) -> List[Dict[str, Any]]:
        try:
            resp = self._http.get(url, headers=NSE_HEADERS)
            resp.raise_for_status()
            data = resp.json()
            # NSE responses are typically either a bare list or {"data": [...]}
            return data if isinstance(data, list) else data.get("data", [])
        except Exception as exc:
            logger.error("IPO fetch failed for %s: %s", url, exc)
            return []

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def fetch_current_ipos(self) -> List[Dict[str, Any]]:
        """IPOs currently open for subscription."""
        records = self._get(NSE_CURRENT_IPO_URL)
        result = [self._normalize(r, "open", NSE_CURRENT_IPO_URL) for r in records]
        logger.info("Fetched %d current IPOs", len(result))
        return result

    def fetch_upcoming_ipos(self) -> List[Dict[str, Any]]:
        """IPOs announced but not yet open for subscription."""
        records = self._get(NSE_UPCOMING_IPO_URL)
        result = [self._normalize(r, "upcoming", NSE_UPCOMING_IPO_URL) for r in records]
        logger.info("Fetched %d upcoming IPOs", len(result))
        return result

    def fetch_recently_listed_ipos(self, months: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        IPOs that have already listed, within the lookback window.

        Args:
            months: how many months back counts as "recently listed". Defaults to
                    config.ipo.lookback_months (config/default.yaml).
        """
        months = months if months is not None else self.cfg.ipo.lookback_months
        cutoff = datetime.utcnow() - timedelta(days=months * 30)

        records = self._get(NSE_PAST_IPO_URL)
        result = []
        for r in records:
            normalized = self._normalize(r, "listed", NSE_PAST_IPO_URL)
            listing_date = self._parse_date(normalized.get("listing_date"))
            if listing_date is None or listing_date >= cutoff:
                normalized["days_since_listing"] = (
                    (datetime.utcnow() - listing_date).days if listing_date else None
                )
                result.append(normalized)

        logger.info(
            "Fetched %d recently-listed IPOs (last %d months)", len(result), months
        )
        return result

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
