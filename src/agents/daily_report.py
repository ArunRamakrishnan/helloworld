"""Daily Morning Report — runs all agents on a watchlist and produces a ranked report."""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.agents.orchestrator import Orchestrator
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Default categories in the morning report
REPORT_CATEGORIES = [
    "top_buffett_stocks",       # High ROE, moat, low debt
    "top_growth_stocks",        # High revenue/profit CAGR, good PEG
    "top_small_cap_opportunities",  # Unicorn score, small cap
    "top_emerging_theme_stocks",    # Emerging sector tailwinds
    "top_dividend_stocks",      # Dividend yield, stable earnings
    "top_fisher_stocks",        # Philip Fisher score
    "stocks_to_avoid",          # High risk score, red flags
]


def _score_buffett(report: Dict) -> float:
    """Buffett: High ROE, strong moat, low debt, positive FCF."""
    roe = report.get("roe") or 0
    moat = report.get("moat_score") or 0
    risk = report.get("risk_score") or 10
    fs = report.get("financial_strength_score") or 0
    return (roe * 100 * 0.3) + (moat * 0.3) + ((10 - risk) * 0.2) + (fs * 0.2)


def _score_growth(report: Dict) -> float:
    """Lynch: Revenue CAGR, profit CAGR, PEG ratio."""
    rev_cagr = (report.get("revenue_cagr_3y") or 0) * 100
    profit_cagr = (report.get("profit_cagr_3y") or 0) * 100
    growth_score = report.get("growth_score") or 0
    peg = report.get("peg_ratio")
    peg_score = max(0, 10 - (peg or 5)) if peg else 5
    return (rev_cagr * 0.25) + (profit_cagr * 0.25) + (growth_score * 0.3) + (peg_score * 0.2)


def _score_small_cap(report: Dict) -> float:
    """Unicorn: Small cap + high unicorn score + low risk."""
    unicorn = report.get("unicorn_score") or 0
    risk = report.get("risk_score") or 10
    is_small = 1.0 if report.get("unicorn_size") == "small_cap" else 0.5 if report.get("unicorn_size") == "mid_cap" else 0
    return (unicorn * 0.5) + ((10 - risk) * 0.3) + (is_small * 2.0)


def _score_emerging_theme(report: Dict) -> float:
    """Emerging themes: unicorn score + number of emerging themes + sentiment."""
    unicorn = report.get("unicorn_score") or 0
    themes = len(report.get("emerging_themes") or [])
    sentiment_score = report.get("sentiment_score") or 5
    return (unicorn * 0.4) + (themes * 1.5) + (sentiment_score * 0.2)


def _score_dividend(report: Dict) -> float:
    """Dividend: yield, financial strength, low risk."""
    div_yield = (report.get("dividend_yield") or 0) * 100
    fs = report.get("financial_strength_score") or 0
    risk = report.get("risk_score") or 10
    return (div_yield * 2.0) + (fs * 0.3) + ((10 - risk) * 0.2)


def _score_fisher(report: Dict) -> float:
    """Fisher: fisher_score, ten_x_potential, growth_ceiling."""
    fisher = report.get("fisher_score") or 0
    ten_x = 2.0 if report.get("ten_x_potential") else 0
    ceiling = {"high": 2.0, "medium": 1.0, "low": 0.0}.get(report.get("growth_ceiling") or "low", 0)
    return fisher + ten_x + ceiling


def _score_avoid(report: Dict) -> float:
    """Avoid: high risk score + red flags."""
    risk = report.get("risk_score") or 0
    flags = len(report.get("red_flags") or [])
    return risk + flags


def _pick_top(
    reports: List[Dict],
    score_fn,
    n: int = 3,
    reverse: bool = True,
    min_score: Optional[float] = None,
) -> List[Dict]:
    scored = [(score_fn(r), r) for r in reports if r.get("final_rating") != "error"]
    scored.sort(key=lambda x: x[0], reverse=reverse)
    result = []
    for score, r in scored[:n]:
        if min_score is not None and score < min_score:
            continue
        result.append({
            "ticker": r["ticker"],
            "final_rating": r.get("final_rating"),
            "category": r.get("category"),
            "score": round(score, 2),
            "current_price": r.get("current_price"),
            "key_metrics": {
                "roe_pct": round((r.get("roe") or 0) * 100, 1),
                "revenue_cagr_3y_pct": round((r.get("revenue_cagr_3y") or 0) * 100, 1),
                "moat_score": r.get("moat_score"),
                "fisher_score": r.get("fisher_score"),
                "unicorn_score": r.get("unicorn_score"),
                "risk_score": r.get("risk_score"),
                "pe_ratio": r.get("pe_ratio"),
                "dividend_yield_pct": round((r.get("dividend_yield") or 0) * 100, 2),
                "emerging_themes": r.get("emerging_themes", []),
                "ten_x_potential": r.get("ten_x_potential"),
                "ten_x_candidate": r.get("ten_x_candidate"),
            },
            "synopsis": r.get("business_summary", ""),
            "bull_case": r.get("bull_case", []),
            "bear_case": r.get("bear_case", []),
            "red_flags": [f.get("key") for f in r.get("red_flags", [])],
        })
    return result


class DailyReportOrchestrator:
    """
    Runs the full research pipeline on a watchlist of stocks and produces
    the morning report with Top 3 picks per category.
    """

    def __init__(self, config=None):
        self.cfg = config or get_config()
        self.orchestrator = Orchestrator(config=self.cfg)
        # Disclaimer text always comes from the real loaded config (see
        # fundamental_agent.py).
        self.disclaimer = get_config().disclaimer

    def run(self, watchlist: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Args:
            watchlist: list of stock dicts, each with the same fields as ResearchRequest.
                       Required keys: ticker, current_price, market_cap_cr, business_description
                       Optional: eps, book_value_per_share, debt_cr, cash_cr, ebitda_cr,
                                 fcf_cr, shares_outstanding_cr, dividend_per_share, statements

        Returns:
            Morning report dict with top picks per category.
        """
        logger.info("=== Daily Report: processing %d stocks ===", len(watchlist))
        reports = []
        for stock in watchlist:
            ticker = stock.get("ticker", "UNKNOWN")
            try:
                report = self.orchestrator.research(
                    ticker=ticker,
                    current_price=stock["current_price"],
                    market_cap_cr=stock["market_cap_cr"],
                    statements=stock.get("statements", []),
                    business_description=stock["business_description"],
                    eps=stock.get("eps"),
                    book_value_per_share=stock.get("book_value_per_share"),
                    debt_cr=stock.get("debt_cr", 0.0),
                    cash_cr=stock.get("cash_cr", 0.0),
                    ebitda_cr=stock.get("ebitda_cr", 0.0),
                    fcf_cr=stock.get("fcf_cr", 0.0),
                    shares_outstanding_cr=stock.get("shares_outstanding_cr", 1.0),
                    dividend_per_share=stock.get("dividend_per_share", 0.0),
                )
                reports.append(report)
                logger.info("Processed %s | rating=%s", ticker, report.get("final_rating"))
            except Exception as exc:
                logger.error("Failed to process %s: %s", ticker, exc)
                reports.append({"ticker": ticker, "final_rating": "error", "error": str(exc)})

        morning_report = self._build_report(reports)
        logger.info("=== Daily Report complete ===")
        return morning_report

    def _build_report(self, reports: List[Dict]) -> Dict[str, Any]:
        strong = [r for r in reports if r.get("final_rating") == "Strong Research Candidate"]
        watch = [r for r in reports if r.get("final_rating") == "Watch"]
        all_valid = strong + watch

        return {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "stocks_analysed": len(reports),
            "top_buffett_stocks": _pick_top(all_valid, _score_buffett, n=3),
            "top_growth_stocks": _pick_top(all_valid, _score_growth, n=3),
            "top_small_cap_opportunities": _pick_top(all_valid, _score_small_cap, n=3),
            "top_emerging_theme_stocks": _pick_top(all_valid, _score_emerging_theme, n=3),
            "top_dividend_stocks": _pick_top(all_valid, _score_dividend, n=3),
            "top_fisher_stocks": _pick_top(all_valid, _score_fisher, n=3),
            "stocks_to_avoid": _pick_top(reports, _score_avoid, n=5, min_score=3.0),
            "portfolio_rebalancing_note": (
                "Review stocks_to_avoid against your current holdings. "
                "Consider trimming positions with risk_score > 7. "
                "Top Buffett and Fisher picks represent highest quality; "
                "small cap opportunities carry higher risk."
            ),
            "disclaimer": self.disclaimer,
        }
