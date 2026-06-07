"""Valuation Agent — PE, PB, EV/EBITDA, PEG, DCF with margin of safety."""
import math
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger
from src.utils.validators import validate_score

logger = get_logger(__name__)


class ValuationAgent:
    """
    Computes relative and absolute valuations.

    DCF assumptions are shown explicitly so users can challenge them.
    Always applies a margin of safety (20-40%) per Graham's principle.
    """

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
        growth_rate_yr1_5: float = 0.12,
        growth_rate_yr6_10: float = 0.08,
        terminal_growth_rate: float = 0.04,
        discount_rate: float = 0.12,
        shares_outstanding_cr: float = 1.0,
        margin_of_safety: float = 0.30,
    ) -> Dict[str, Any]:
        """
        Conservative two-stage DCF.

        Args:
            fcf_cr: Current free cash flow in crores
            growth_rate_yr1_5: FCF growth rate years 1-5
            growth_rate_yr6_10: FCF growth rate years 6-10
            terminal_growth_rate: Perpetuity growth rate after year 10
            discount_rate: Required rate of return (WACC)
            shares_outstanding_cr: Shares in crores
            margin_of_safety: Discount applied to intrinsic value

        Returns dict with intrinsic_value_per_share, margin_of_safety_applied, assumptions.
        """
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
        if pe is None:
            return 5.0
        if pe <= 10:
            return 10.0
        if pe <= 15:
            return 8.0
        if pe <= 20:
            return 6.0
        if pe <= 30:
            return 4.0
        if pe <= 50:
            return 2.0
        return 0.0

    def score_pb(self, pb: Optional[float]) -> float:
        """Graham: PB < 1.5 is attractive."""
        if pb is None:
            return 5.0
        if pb <= 1.0:
            return 10.0
        if pb <= 1.5:
            return 8.0
        if pb <= 3.0:
            return 5.0
        if pb <= 5.0:
            return 3.0
        return 1.0

    def score_peg(self, peg: Optional[float]) -> float:
        """Lynch: PEG < 1 is undervalued growth."""
        if peg is None:
            return 5.0
        if peg <= 0.5:
            return 10.0
        if peg <= 1.0:
            return 8.0
        if peg <= 1.5:
            return 5.0
        if peg <= 2.0:
            return 3.0
        return 1.0

    def score_margin_of_safety(self, current_price: float, intrinsic_value: Optional[float]) -> float:
        """Score based on how far below intrinsic value the stock is trading."""
        if intrinsic_value is None or intrinsic_value <= 0:
            return 5.0
        discount = (intrinsic_value - current_price) / intrinsic_value
        if discount >= 0.40:
            return 10.0
        if discount >= 0.25:
            return 8.0
        if discount >= 0.10:
            return 6.0
        if discount >= 0:
            return 4.0
        return 1.0  # trading above intrinsic value

    def overall_valuation_score(
        self,
        pe: Optional[float],
        pb: Optional[float],
        peg: Optional[float],
        current_price: float,
        intrinsic_value: Optional[float],
    ) -> float:
        scores = [
            (self.score_pe(pe), 0.25),
            (self.score_pb(pb), 0.25),
            (self.score_peg(peg), 0.25),
            (self.score_margin_of_safety(current_price, intrinsic_value), 0.25),
        ]
        result = sum(s * w for s, w in scores)
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
