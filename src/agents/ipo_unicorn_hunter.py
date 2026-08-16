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

        ipo_records: List[Dict[str, Any]] = []
        if symbol_list is None:
            ipo_records = self.ipo_agent.fetch_recently_listed_ipos(months=months)
            symbols = [r["symbol"] for r in ipo_records if r.get("symbol")]
        else:
            symbols = symbol_list

        if not symbols:
            return {
                "total_scanned": 0,
                "passed_filter": 0,
                "candidates": [],
                "candidates_returned": 0,
                "ipo_lookback_months": months if months is not None else self.cfg.ipo.lookback_months,
                "hunt_note": (
                    "No recently-listed IPOs found to scan. NSE's IPO endpoint may be "
                    "unreachable, or none listed within the lookback window — try "
                    "passing an explicit symbol_list."
                ),
            }

        ipo_by_symbol = {r["symbol"]: r for r in ipo_records if r.get("symbol")}

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
        result["ipo_lookback_months"] = months if months is not None else self.cfg.ipo.lookback_months
        result["hunt_note"] = (
            f"Scanned {len(symbols)} IPOs listed within the last "
            f"{result['ipo_lookback_months']} months. {result['passed_filter']} passed "
            f"the growth + quality pre-filter. Ranked by unicorn composite score "
            f"(growth × theme × quality × valuation) plus a listing-recency bonus."
        )
        return result

    def close(self):
        self.ipo_agent.close()
