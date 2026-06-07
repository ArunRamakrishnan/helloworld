"""Fundamental Analysis Agent — computes financial ratios and scores from raw statement data."""
import math
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger
from src.utils.validators import validate_score

logger = get_logger(__name__)


def _cagr(start: float, end: float, years: int) -> Optional[float]:
    """Compound Annual Growth Rate. Returns None if inputs are invalid."""
    if years <= 0 or start is None or end is None or start <= 0:
        return None
    return (end / start) ** (1 / years) - 1


class FundamentalAgent:
    """
    Calculates:
    - Revenue CAGR, Profit CAGR
    - EBITDA margin trend
    - ROE, ROCE
    - Debt/Equity ratio
    - Interest coverage ratio
    - Free Cash Flow (FCF)
    - Working capital cycle
    - Promoter holding and pledge trend
    - Dividend history

    Scoring: all scores are /10, with 10 being the best.
    """

    # ------------------------------------------------------------------
    # CAGR calculations
    # ------------------------------------------------------------------

    def revenue_cagr(self, statements: List[Dict[str, Any]], years: int = 3) -> Optional[float]:
        """Revenue CAGR over the given number of years from annual statements."""
        annuals = [s for s in statements if s.get("period_type") == "annual"]
        annuals_sorted = sorted(annuals, key=lambda x: x.get("period", ""))
        if len(annuals_sorted) < years + 1:
            return None
        start = annuals_sorted[-(years + 1)].get("revenue_cr")
        end = annuals_sorted[-1].get("revenue_cr")
        return _cagr(start, end, years)

    def profit_cagr(self, statements: List[Dict[str, Any]], years: int = 3) -> Optional[float]:
        """Net profit CAGR over the given number of years."""
        annuals = sorted(
            [s for s in statements if s.get("period_type") == "annual"],
            key=lambda x: x.get("period", ""),
        )
        if len(annuals) < years + 1:
            return None
        start = annuals[-(years + 1)].get("net_profit_cr")
        end = annuals[-1].get("net_profit_cr")
        if start is None or end is None or start <= 0:
            return None
        return _cagr(start, end, years)

    # ------------------------------------------------------------------
    # Ratio computations
    # ------------------------------------------------------------------

    def compute_roe(self, net_profit_cr: float, equity_cr: float) -> Optional[float]:
        if not equity_cr or equity_cr == 0:
            return None
        return net_profit_cr / equity_cr

    def compute_roce(
        self, ebit_cr: float, total_assets_cr: float, current_liabilities_cr: float
    ) -> Optional[float]:
        capital_employed = total_assets_cr - current_liabilities_cr
        if capital_employed <= 0:
            return None
        return ebit_cr / capital_employed

    def compute_debt_equity(self, debt_cr: float, equity_cr: float) -> Optional[float]:
        if not equity_cr or equity_cr == 0:
            return None
        return debt_cr / equity_cr

    def compute_interest_coverage(self, ebit_cr: float, interest_cr: float) -> Optional[float]:
        if not interest_cr or interest_cr == 0:
            return None
        return ebit_cr / interest_cr

    def compute_fcf(self, operating_cash_flow_cr: float, capex_cr: float) -> float:
        return operating_cash_flow_cr - abs(capex_cr)

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def score_roe(self, roe: Optional[float]) -> float:
        """Score ROE: Buffett likes ROE > 15% consistently."""
        if roe is None:
            return 0.0
        if roe >= 0.30:
            return 10.0
        if roe >= 0.20:
            return 8.0
        if roe >= 0.15:
            return 6.0
        if roe >= 0.10:
            return 4.0
        if roe > 0:
            return 2.0
        return 0.0

    def score_debt_equity(self, de: Optional[float]) -> float:
        """Score D/E: Graham prefers D/E < 0.5; high debt is risky."""
        if de is None:
            return 5.0
        if de <= 0:
            return 10.0
        if de <= 0.5:
            return 8.0
        if de <= 1.0:
            return 6.0
        if de <= 2.0:
            return 4.0
        return 1.0

    def score_revenue_cagr(self, cagr: Optional[float]) -> float:
        """Score revenue CAGR: Lynch likes consistent 15%+ growth."""
        if cagr is None:
            return 0.0
        if cagr >= 0.20:
            return 10.0
        if cagr >= 0.15:
            return 8.0
        if cagr >= 0.10:
            return 6.0
        if cagr >= 0.05:
            return 4.0
        if cagr > 0:
            return 2.0
        return 0.0

    def score_fcf(self, fcf: float, revenue_cr: float) -> float:
        """Score FCF as % of revenue — positive FCF is a quality sign."""
        if revenue_cr <= 0:
            return 0.0
        ratio = fcf / revenue_cr
        if ratio >= 0.15:
            return 10.0
        if ratio >= 0.10:
            return 8.0
        if ratio >= 0.05:
            return 6.0
        if ratio > 0:
            return 4.0
        return 1.0

    def overall_financial_strength_score(
        self,
        roe: Optional[float],
        de: Optional[float],
        rev_cagr: Optional[float],
        fcf: float,
        revenue_cr: float,
    ) -> float:
        """Weighted average of sub-scores, /10."""
        scores = [
            (self.score_roe(roe), 0.30),
            (self.score_debt_equity(de), 0.25),
            (self.score_revenue_cagr(rev_cagr), 0.25),
            (self.score_fcf(fcf, revenue_cr), 0.20),
        ]
        result = sum(s * w for s, w in scores)
        return round(validate_score(result, "financial_strength_score"), 2)

    def analyze(self, ticker: str, statements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run full fundamental analysis on a stock. Returns scored dict."""
        logger.info("Fundamental analysis for %s", ticker)
        if not statements:
            return {"ticker": ticker, "error": "No financial statements provided"}

        latest = sorted(
            [s for s in statements if s.get("period_type") == "annual"],
            key=lambda x: x.get("period", ""),
        )
        latest = latest[-1] if latest else {}

        rev_cr = latest.get("revenue_cr", 0) or 0
        net_profit_cr = latest.get("net_profit_cr", 0) or 0
        equity_cr = latest.get("total_equity_cr", 0) or 0
        debt_cr = latest.get("total_debt_cr", 0) or 0
        capex_cr = latest.get("capex_cr", 0) or 0
        fcf_cr = latest.get("free_cash_flow_cr") or self.compute_fcf(
            net_profit_cr, capex_cr
        )

        roe = self.compute_roe(net_profit_cr, equity_cr)
        de = self.compute_debt_equity(debt_cr, equity_cr)
        rev_cagr = self.revenue_cagr(statements)
        profit_cagr = self.profit_cagr(statements)

        score = self.overall_financial_strength_score(roe, de, rev_cagr, fcf_cr, rev_cr)

        return {
            "ticker": ticker,
            "roe": roe,
            "debt_equity": de,
            "revenue_cagr_3y": rev_cagr,
            "profit_cagr_3y": profit_cagr,
            "fcf_cr": fcf_cr,
            "promoter_holding_pct": latest.get("promoter_holding_pct"),
            "promoter_pledge_pct": latest.get("promoter_pledge_pct"),
            "financial_strength_score": score,
        }
