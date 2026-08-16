"""IPO Unicorn Hunter — which recently-listed IPOs are best positioned to become the
next NIFTY 50 candidate.

Reuses UnicornHunterAgent's growth/quality/theme scan (the same investment-framework
scoring the rest of this project uses — Lynch-style growth, Graham/Buffett-style
quality and debt discipline, sector-tailwind theme detection) rather than duplicating
it, and scopes the universe to freshly-listed IPOs instead of the static
UNICORN_UNIVERSE list. Adds IPO-specific context: listing date, issue price band,
listing gain, and a recency bonus (config.scoring.ipo_unicorn) since a stock still
close to its IPO is, almost by definition, less "discovered" than one that's been
trading for years.

`hunt()` distinguishes four outcomes rather than collapsing every non-result into
"no candidates" — the difference between "NSE was unreachable" and "NSE has no fresh
IPOs to score" and "IPOs exist but none look like unicorns" matters for diagnosis:
  - "data_unavailable"   — the NSE fetch itself failed (see result["funnel"]["nse_fetch"])
  - "no_ipos_in_window"  — NSE responded, but no IPOs listed in the lookback window
  - "no_candidates"      — IPOs were scanned but none passed/scored as unicorns
  - "ok"                 — at least one candidate was found
"""
from typing import Any, Dict, List, Optional

from src.agents.ipo_agent import IPODataAgent
from src.agents.registry import AgentRegistry
from src.agents.unicorn_hunter import UnicornHunterAgent
from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.scoring import tiered_score

logger = get_logger(__name__)


@AgentRegistry.register("ipo_unicorn_hunter")
class IPOUnicornHunterAgent:
    """
    Loads all IPOs listed within the lookback window (config.ipo.lookback_months) and
    ranks them for next-unicorn potential.
    """

    def __init__(self, config=None):
        self.cfg = config or get_config()
        # Recency-bonus rules always come from the real loaded config, independent of
        # whatever `config` object the caller injects (see fundamental_agent.py).
        self.rules = get_config().scoring.ipo_unicorn
        self.ipo_agent = IPODataAgent(config=self.cfg)
        self.unicorn_hunter = UnicornHunterAgent(config=self.cfg)

    def _recency_bonus(self, days_since_listing: Optional[int]) -> float:
        return tiered_score(
            days_since_listing,
            self.rules.recency_bonus_tiers,
            no_match=self.rules.recency_bonus_no_match,
            if_none=self.rules.recency_bonus_no_match,
            mode="lte",
        )

    def hunt(
        self,
        symbol_list: Optional[List[str]] = None,
        months: Optional[int] = None,
        top_n: Optional[int] = None,
        progress_callback=None,
    ) -> Dict[str, Any]:
        """
        Args:
            symbol_list: override universe of IPO tickers. If None, pulled live from
                         IPODataAgent.fetch_recently_listed_ipos(months).
            months: "recently listed" lookback window in months (defaults to
                    config.ipo.lookback_months).
            top_n: how many ranked candidates to return (defaults to
                   config.ipo.default_top_n).
            progress_callback: optional callable(done, total), forwarded to the scan.
        """
        top_n = top_n if top_n is not None else self.cfg.ipo.default_top_n
        lookback_months = months if months is not None else self.cfg.ipo.lookback_months

        funnel: Dict[str, Any] = {
            "nse_fetch": None,
            "ipo_records_received": 0,
            "lookback_days": lookback_months * 30,
            "after_date_filter": 0,
            "unicorn_prefilter_passed": 0,
            "unicorn_candidates": 0,
        }

        ipo_by_symbol: Dict[str, Any] = {}
        if symbol_list is None:
            fetch = self.ipo_agent.fetch_recently_listed_ipos(months=months)
            funnel["nse_fetch"] = fetch["status"]
            funnel["ipo_records_received"] = fetch.get("total_received", 0)
            funnel["after_date_filter"] = fetch.get("total_after_date_filter", len(fetch["records"]))

            if fetch["status"] != "ok":
                logger.error("IPO unicorn hunt aborted — NSE IPO data unavailable: %s", fetch["error"])
                return self._early_result(
                    status="data_unavailable",
                    hunt_note=(
                        f"NSE IPO data unavailable ({fetch['error']}). This usually means "
                        f"NSE's IPO endpoint rejected/blocked the request rather than there "
                        f"being no IPOs — retry shortly, or pass an explicit symbol_list."
                    ),
                    funnel=funnel, lookback_months=lookback_months,
                )

            symbols = [r["symbol"] for r in fetch["records"] if r.get("symbol")]
            ipo_by_symbol = {r["symbol"]: r for r in fetch["records"] if r.get("symbol")}

            if not symbols:
                logger.info("IPO unicorn hunt: 0 IPOs listed in the last %d days", funnel["lookback_days"])
                return self._early_result(
                    status="no_ipos_in_window",
                    hunt_note=(
                        f"NSE IPO data fetched successfully, but no IPOs were listed in the "
                        f"last {lookback_months} months. Try widening lookback_months."
                    ),
                    funnel=funnel, lookback_months=lookback_months,
                )
        else:
            symbols = symbol_list
            funnel["nse_fetch"] = "skipped (explicit symbol_list)"
            funnel["ipo_records_received"] = len(symbols)
            funnel["after_date_filter"] = len(symbols)

        logger.info(
            "IPO unicorn hunt funnel | nse_fetch=%s | received=%d | after_date_filter=%d",
            funnel["nse_fetch"], funnel["ipo_records_received"], funnel["after_date_filter"],
        )

        # Delegate the actual fundamentals/growth/quality/theme scan to
        # UnicornHunterAgent — same framework as the broader unicorn hunt, scoped to
        # the IPO universe instead of the static UNICORN_UNIVERSE list. Ask it to
        # return everything that passed the filter so we can merge IPO metadata and
        # re-rank (with the recency bonus) before trimming to top_n ourselves.
        result = self.unicorn_hunter.hunt(
            symbol_list=symbols,
            top_n=len(symbols),
            progress_callback=progress_callback,
        )
        funnel["unicorn_prefilter_passed"] = result.get("passed_filter", 0)

        for candidate in result["candidates"]:
            ipo_info = ipo_by_symbol.get(candidate["ticker"], {})
            days_since_listing = ipo_info.get("days_since_listing")
            bonus = self._recency_bonus(days_since_listing)
            issue_price_max = ipo_info.get("issue_price_max")
            current_price = candidate.get("current_price")

            candidate["ipo_listing_date"] = ipo_info.get("listing_date")
            candidate["ipo_issue_price_min"] = ipo_info.get("issue_price_min")
            candidate["ipo_issue_price_max"] = issue_price_max
            candidate["days_since_listing"] = days_since_listing
            candidate["ipo_recency_bonus"] = bonus
            candidate["listing_gain_pct"] = (
                round((current_price - issue_price_max) / issue_price_max * 100, 2)
                if issue_price_max and current_price
                else None
            )
            candidate["unicorn_composite"] = round(
                min(10.0, candidate.get("unicorn_composite", 0) + bonus), 2
            )

        result["candidates"].sort(key=lambda c: c.get("unicorn_composite", 0), reverse=True)
        result["candidates"] = result["candidates"][:top_n]
        result["candidates_returned"] = len(result["candidates"])
        result["ipo_lookback_months"] = lookback_months
        funnel["unicorn_candidates"] = result["candidates_returned"]
        result["funnel"] = funnel

        logger.info(
            "IPO unicorn hunt funnel | prefilter_passed=%d | candidates=%d",
            funnel["unicorn_prefilter_passed"], funnel["unicorn_candidates"],
        )

        if result["candidates_returned"] == 0:
            result["status"] = "no_candidates"
            result["hunt_note"] = (
                f"{len(symbols)} IPOs found within the last {lookback_months} months, but none "
                f"matched unicorn criteria — {funnel['unicorn_prefilter_passed']} passed the "
                f"growth/quality pre-filter (market cap, revenue, debt) but none scored high "
                f"enough, or yfinance had no usable data for the rest "
                f"({result.get('fetch_failures', 0)} fetch failures). Not the same as "
                f"'no IPOs found' — check result['funnel'] for where the pipeline narrowed."
            )
        else:
            result["status"] = "ok"
            result["hunt_note"] = (
                f"Scanned {len(symbols)} IPOs listed within the last {lookback_months} months. "
                f"{funnel['unicorn_prefilter_passed']} passed the growth + quality pre-filter. "
                f"Ranked by unicorn composite score (growth × theme × quality × valuation) "
                f"plus a listing-recency bonus."
            )
        return result

    @staticmethod
    def _early_result(status: str, hunt_note: str, funnel: Dict[str, Any], lookback_months: int) -> Dict[str, Any]:
        return {
            "status": status,
            "hunt_note": hunt_note,
            "funnel": funnel,
            "total_scanned": 0,
            "passed_filter": 0,
            "fetch_failures": 0,
            "filtered_out": 0,
            "candidates": [],
            "candidates_returned": 0,
            "theme_breakdown": {},
            "ipo_lookback_months": lookback_months,
        }

    def close(self):
        self.ipo_agent.close()
