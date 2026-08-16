"""Valuation Agent — PE, PB, EV/EBITDA, PEG, DCF with margin of safety."""
import math
from typing import Any, Dict, List, Optional

from src.agents.registry import AgentRegistry
from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.scoring import tiered_score, weighted_average
from src.utils.validators import validate_score

logger = get_logger(__name__)


@AgentRegistry.register("valuation")
class ValuationAgent:
    """
    Computes relative and absolute valuations.

    DCF assumptions are shown explicitly so users can challenge them.
    Always applies a margin of safety (20-40%) per Graham's principle.
    All thresholds/weights/DCF defaults are sourced from
    config.scoring.valuation (config/default.yaml).
    """

    def __init__(self, config=None):
        self.cfg = config or get_config()
        # Scoring rules always come from the real loaded config, independent of
        # whatever `config` object the caller injects (see fundamental_agent.py).
        self.rules = get_config().scoring.valuation

    # ------------------------------------------------------------------
    # Ratio calculations
    # ------------------------------------------------------------------

    def pe_ratio(self, price: float, eps: float) -> Optional[float]:
        if eps is None or eps <= 0:
            return None
        return price / eps

    def pb_ratio(self, price: float, book_value_per_share: float) -> Optional[float]:
        if book_value_per_share is None or book_value_per_share <= 0:
            return None
        return price / book_value_per_share

    def ev_ebitda(
        self,
        market_cap_cr: float,
        debt_cr: float,
        cash_cr: float,
        ebitda_cr: float,
    ) -> Optional[float]:
        if ebitda_cr is None or ebitda_cr <= 0:
            return None
        ev = market_cap_cr + debt_cr - cash_cr
        return ev / ebitda_cr

    def peg_ratio(self, pe: Optional[float], earnings_growth_pct: float) -> Optional[float]:
        """PEG = PE / earnings growth rate (%). Lynch: PEG < 1 is attractive."""
        if pe is None or earnings_growth_pct is None or earnings_growth_pct <= 0:
            return None
        return pe / earnings_growth_pct

    def dividend_yield(self, dividend_per_share: float, price: float) -> Optional[float]:
        if price <= 0:
            return None
        return dividend_per_share / price

    # ------------------------------------------------------------------
    # DCF
    # ------------------------------------------------------------------

    def dcf_intrinsic_value(
        self,
        fcf_cr: float,
        growth_rate_yr1_5: Optional[float] = None,
        growth_rate_yr6_10: Optional[float] = None,
        terminal_growth_rate: Optional[float] = None,
        discount_rate: Optional[float] = None,
        shares_outstanding_cr: float = 1.0,
        margin_of_safety: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Conservative two-stage DCF.

        Args:
            fcf_cr: Current free cash flow in crores
            growth_rate_yr1_5: FCF growth rate years 1-5 (defaults from config)
            growth_rate_yr6_10: FCF growth rate years 6-10 (defaults from config)
            terminal_growth_rate: Perpetuity growth rate after year 10 (defaults from config)
            discount_rate: Required rate of return / WACC (defaults from config)
            shares_outstanding_cr: Shares in crores
            margin_of_safety: Discount applied to intrinsic value (defaults from config)

        Returns dict with intrinsic_value_per_share, margin_of_safety_applied, assumptions.
        """
        d = self.rules.dcf_defaults
        growth_rate_yr1_5 = d.growth_rate_yr1_5 if growth_rate_yr1_5 is None else growth_rate_yr1_5
        growth_rate_yr6_10 = d.growth_rate_yr6_10 if growth_rate_yr6_10 is None else growth_rate_yr6_10
        terminal_growth_rate = d.terminal_growth_rate if terminal_growth_rate is None else terminal_growth_rate
        discount_rate = d.discount_rate if discount_rate is None else discount_rate
        margin_of_safety = d.margin_of_safety if margin_of_safety is None else margin_of_safety

        if fcf_cr <= 0:
            return {
                "intrinsic_value_per_share": None,
                "error": "Negative or zero FCF — DCF not reliable",
                "assumptions": {},
            }

        pv_total = 0.0
        cf = fcf_cr
        for yr in range(1, 11):
            rate = growth_rate_yr1_5 if yr <= 5 else growth_rate_yr6_10
            cf = cf * (1 + rate)
            pv_total += cf / ((1 + discount_rate) ** yr)

        terminal_value = (cf * (1 + terminal_growth_rate)) / (discount_rate - terminal_growth_rate)
        pv_terminal = terminal_value / ((1 + discount_rate) ** 10)
        total_value_cr = pv_total + pv_terminal

        if shares_outstanding_cr <= 0:
            shares_outstanding_cr = 1.0
        intrinsic_raw = total_value_cr / shares_outstanding_cr  # in crores per crore shares = rupees
        intrinsic_with_mos = intrinsic_raw * (1 - margin_of_safety)

        logger.info(
            "DCF complete | intrinsic=%.2f | with MoS(%.0f%%)=%.2f",
            intrinsic_raw, margin_of_safety * 100, intrinsic_with_mos,
        )
        return {
            "intrinsic_value_per_share_raw": round(intrinsic_raw, 2),
            "intrinsic_value_per_share_with_mos": round(intrinsic_with_mos, 2),
            "margin_of_safety_applied_pct": margin_of_safety * 100,
            "pv_cash_flows_cr": round(pv_total, 2),
            "pv_terminal_value_cr": round(pv_terminal, 2),
            "assumptions": {
                "fcf_start_cr": fcf_cr,
                "growth_yr1_5_pct": growth_rate_yr1_5 * 100,
                "growth_yr6_10_pct": growth_rate_yr6_10 * 100,
                "terminal_growth_pct": terminal_growth_rate * 100,
                "discount_rate_pct": discount_rate * 100,
            },
        }

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def score_pe(self, pe: Optional[float], sector_median_pe: Optional[float] = None) -> float:
        """Graham benchmark: PE < 15 is value territory."""
        return tiered_score(
            pe, self.rules.pe_tiers,
            no_match=self.rules.pe_no_match, if_none=self.rules.pe_if_none, mode="lte",
        )

    def score_pb(self, pb: Optional[float]) -> float:
        """Graham: PB < 1.5 is attractive."""
        return tiered_score(
            pb, self.rules.pb_tiers,
            no_match=self.rules.pb_no_match, if_none=self.rules.pb_if_none, mode="lte",
        )

    def score_peg(self, peg: Optional[float]) -> float:
        """Lynch: PEG < 1 is undervalued growth."""
        return tiered_score(
            peg, self.rules.peg_tiers,
            no_match=self.rules.peg_no_match, if_none=self.rules.peg_if_none, mode="lte",
        )

    def score_margin_of_safety(self, current_price: float, intrinsic_value: Optional[float]) -> float:
        """Score based on how far below intrinsic value the stock is trading."""
        if intrinsic_value is None or intrinsic_value <= 0:
            return self.rules.margin_of_safety_if_none
        discount = (intrinsic_value - current_price) / intrinsic_value
        return tiered_score(
            discount, self.rules.margin_of_safety_tiers,
            no_match=self.rules.margin_of_safety_no_match,
        )

    def overall_valuation_score(
        self,
        pe: Optional[float],
        pb: Optional[float],
        peg: Optional[float],
        current_price: float,
        intrinsic_value: Optional[float],
    ) -> float:
        w = self.rules.weights
        scores = [
            (self.score_pe(pe), w["pe"]),
            (self.score_pb(pb), w["pb"]),
            (self.score_peg(peg), w["peg"]),
            (self.score_margin_of_safety(current_price, intrinsic_value), w["margin_of_safety"]),
        ]
        result = weighted_average(scores)
        return round(validate_score(result, "valuation_score"), 2)

    def analyze(
        self,
        ticker: str,
        current_price: float,
        market_cap_cr: float,
        eps: Optional[float],
        book_value_per_share: Optional[float],
        debt_cr: float,
        cash_cr: float,
        ebitda_cr: float,
        fcf_cr: float,
        shares_outstanding_cr: float,
        profit_cagr: Optional[float],
        dividend_per_share: float = 0.0,
    ) -> Dict[str, Any]:
        logger.info("Valuation analysis for %s @ price=%.2f", ticker, current_price)

        pe = self.pe_ratio(current_price, eps)
        pb = self.pb_ratio(current_price, book_value_per_share)
        ev_eb = self.ev_ebitda(market_cap_cr, debt_cr, cash_cr, ebitda_cr)
        earnings_growth_pct = (profit_cagr or 0) * 100
        peg = self.peg_ratio(pe, earnings_growth_pct)
        div_yield = self.dividend_yield(dividend_per_share, current_price)
        dcf = self.dcf_intrinsic_value(fcf_cr, shares_outstanding_cr=shares_outstanding_cr)
        intrinsic = dcf.get("intrinsic_value_per_share_with_mos")

        valuation_score = self.overall_valuation_score(pe, pb, peg, current_price, intrinsic)

        return {
            "ticker": ticker,
            "current_price": current_price,
            "pe_ratio": pe,
            "pb_ratio": pb,
            "ev_ebitda": ev_eb,
            "peg_ratio": peg,
            "dividend_yield": div_yield,
            "dcf": dcf,
            "intrinsic_value_with_mos": intrinsic,
            "valuation_score": valuation_score,
        }
