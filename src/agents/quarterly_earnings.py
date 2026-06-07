"""Quarterly Earnings Agent — fetches and analyses last 4-8 quarters via yfinance.

Detects:
- Revenue and profit growth trends (accelerating / decelerating / flat)
- Margin expansion or compression
- Earnings consistency (no wild swings)
- QoQ and YoY changes for each quarter

TODO: Replace yfinance with Screener.in API for better India-specific quarterly data.
TODO: Add Trendlyne API for consensus estimates and earnings beat/miss tracking.
"""
from typing import Any, Dict, List, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)

INR_TO_CR = 1e7


class QuarterlyEarningsAgent:
    """
    Fetches last 8 quarters of financials from yfinance and computes:
    - Revenue & profit QoQ / YoY growth
    - Margin trends (expanding / compressing)
    - Earnings quality score (consistency, FCF backing)
    - Lynch-style earnings acceleration signal
    """

    def _fetch_quarterly_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch yfinance quarterly financials. Returns raw DataFrames."""
        try:
            import yfinance as yf
            ticker = yf.Ticker(f"{symbol}.NS")
            return {
                "financials": ticker.quarterly_financials,
                "balance_sheet": ticker.quarterly_balance_sheet,
                "cashflow": ticker.quarterly_cashflow,
            }
        except ImportError:
            logger.error("yfinance not installed")
            return {}
        except Exception as exc:
            logger.error("yfinance quarterly fetch failed for %s: %s", symbol, exc)
            return {}

    def _safe_cr(self, df, row_key: str, col_idx: int) -> Optional[float]:
        """Safely extract a value from a DataFrame and convert to crores."""
        try:
            if df is None or df.empty:
                return None
            # Find the row
            matching = [r for r in df.index if row_key.lower() in r.lower()]
            if not matching:
                return None
            row = df.loc[matching[0]]
            if col_idx >= len(row):
                return None
            val = row.iloc[col_idx]
            if val is None or (hasattr(val, '__float__') and val != val):  # NaN check
                return None
            return round(float(val) / INR_TO_CR, 2)
        except Exception:
            return None

    def _pct_change(self, current: Optional[float], previous: Optional[float]) -> Optional[float]:
        if current is None or previous is None or previous == 0:
            return None
        return round((current - previous) / abs(previous), 4)

    def _build_quarters(self, raw: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse raw yfinance DataFrames into list of quarterly dicts."""
        fin = raw.get("financials")
        cf = raw.get("cashflow")

        if fin is None or fin.empty:
            return []

        quarters = []
        num_quarters = min(8, len(fin.columns))

        for i in range(num_quarters):
            try:
                col = fin.columns[i]
                period = str(col)[:10] if hasattr(col, '__str__') else f"Q{i+1}"

                revenue = self._safe_cr(fin, "Total Revenue", i)
                gross_profit = self._safe_cr(fin, "Gross Profit", i)
                ebit = self._safe_cr(fin, "EBIT", i)
                net_income = self._safe_cr(fin, "Net Income", i)
                operating_cf = self._safe_cr(cf, "Operating Cash Flow", i) if cf is not None and not cf.empty else None

                gross_margin = round(gross_profit / revenue, 4) if revenue and gross_profit else None
                ebit_margin = round(ebit / revenue, 4) if revenue and ebit else None
                net_margin = round(net_income / revenue, 4) if revenue and net_income else None

                quarters.append({
                    "period": period,
                    "revenue_cr": revenue,
                    "gross_profit_cr": gross_profit,
                    "ebit_cr": ebit,
                    "net_income_cr": net_income,
                    "operating_cf_cr": operating_cf,
                    "gross_margin": gross_margin,
                    "ebit_margin": ebit_margin,
                    "net_margin": net_margin,
                })
            except Exception as exc:
                logger.debug("Error parsing quarter %d: %s", i, exc)

        return quarters

    def _compute_trends(self, quarters: List[Dict]) -> Dict[str, Any]:
        """Compute QoQ and YoY growth rates and detect trends."""
        if len(quarters) < 2:
            return {"trend": "insufficient_data"}

        # Most recent quarter is index 0 (yfinance returns newest first)
        q0 = quarters[0]
        q1 = quarters[1] if len(quarters) > 1 else {}
        q4 = quarters[4] if len(quarters) > 4 else {}   # same quarter last year
        q_oldest = quarters[-1]

        rev_qoq = self._pct_change(q0.get("revenue_cr"), q1.get("revenue_cr"))
        rev_yoy = self._pct_change(q0.get("revenue_cr"), q4.get("revenue_cr"))
        profit_qoq = self._pct_change(q0.get("net_income_cr"), q1.get("net_income_cr"))
        profit_yoy = self._pct_change(q0.get("net_income_cr"), q4.get("net_income_cr"))

        # Margin trend: compare latest vs 4 quarters ago
        margin_expanding = None
        if q0.get("net_margin") is not None and q4.get("net_margin") is not None:
            margin_expanding = q0["net_margin"] > q4["net_margin"]

        # Earnings acceleration: is growth rate itself growing?
        rev_accel = None
        if len(quarters) >= 4:
            recent_growth = self._pct_change(q0.get("revenue_cr"), q1.get("revenue_cr"))
            older_growth = self._pct_change(q1.get("revenue_cr"), quarters[2].get("revenue_cr"))
            if recent_growth is not None and older_growth is not None:
                rev_accel = recent_growth > older_growth

        # Earnings consistency: count quarters with positive net income
        positive_quarters = sum(1 for q in quarters if (q.get("net_income_cr") or 0) > 0)
        consistency_pct = round(positive_quarters / len(quarters), 2) if quarters else 0

        # FCF backing: is operating cash flow positive?
        fcf_positive_count = sum(1 for q in quarters if (q.get("operating_cf_cr") or 0) > 0)

        return {
            "revenue_qoq_growth": rev_qoq,
            "revenue_yoy_growth": rev_yoy,
            "profit_qoq_growth": profit_qoq,
            "profit_yoy_growth": profit_yoy,
            "margin_expanding": margin_expanding,
            "earnings_accelerating": rev_accel,
            "earnings_consistency_pct": consistency_pct,
            "quarters_with_positive_fcf": fcf_positive_count,
            "total_quarters_analysed": len(quarters),
        }

    def _earnings_quality_score(self, trends: Dict, quarters: List[Dict]) -> float:
        """Score earnings quality 0-10 for use in ranking."""
        score = 5.0  # neutral baseline

        rev_yoy = trends.get("revenue_yoy_growth") or 0
        profit_yoy = trends.get("profit_yoy_growth") or 0

        # Revenue growth bonus
        if rev_yoy >= 0.25: score += 1.5
        elif rev_yoy >= 0.15: score += 1.0
        elif rev_yoy >= 0.08: score += 0.5
        elif rev_yoy < 0: score -= 1.0

        # Profit growth bonus
        if profit_yoy >= 0.25: score += 1.5
        elif profit_yoy >= 0.15: score += 1.0
        elif profit_yoy >= 0.08: score += 0.5
        elif profit_yoy < -0.10: score -= 1.5

        # Margin trend
        if trends.get("margin_expanding"): score += 0.5
        elif trends.get("margin_expanding") is False: score -= 0.5

        # Earnings acceleration (Lynch loves this)
        if trends.get("earnings_accelerating"): score += 0.5

        # Consistency
        consistency = trends.get("earnings_consistency_pct") or 0
        if consistency >= 0.90: score += 0.5
        elif consistency < 0.50: score -= 1.0

        # FCF backing
        fcf_q = trends.get("quarters_with_positive_fcf") or 0
        total_q = trends.get("total_quarters_analysed") or 1
        if fcf_q / total_q >= 0.75: score += 0.5

        return round(min(10.0, max(0.0, score)), 2)

    def analyze(self, ticker: str) -> Dict[str, Any]:
        """
        Fetch and analyse quarterly earnings for a ticker.

        Returns:
            Dict with quarters list, trend analysis, and earnings quality score.
        """
        logger.info("Quarterly earnings analysis for %s", ticker)
        raw = self._fetch_quarterly_data(ticker)

        if not raw:
            return {
                "ticker": ticker,
                "error": "Could not fetch quarterly data",
                "earnings_quality_score": 5.0,
                "quarters": [],
                "trends": {},
            }

        quarters = self._build_quarters(raw)
        if not quarters:
            return {
                "ticker": ticker,
                "error": "No quarterly financial data available",
                "earnings_quality_score": 5.0,
                "quarters": [],
                "trends": {},
            }

        trends = self._compute_trends(quarters)
        eq_score = self._earnings_quality_score(trends, quarters)

        logger.info(
            "Quarterly analysis complete for %s | rev_yoy=%.1f%% | eq_score=%.1f",
            ticker,
            (trends.get("revenue_yoy_growth") or 0) * 100,
            eq_score,
        )

        return {
            "ticker": ticker,
            "earnings_quality_score": eq_score,
            "quarters": quarters[:4],   # Return last 4 quarters in response
            "trends": trends,
            "latest_quarter": quarters[0] if quarters else {},
        }
