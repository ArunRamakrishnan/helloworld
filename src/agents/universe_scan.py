"""Universe Scan Orchestrator — Two-stage full NSE/BSE scan with Top 10 per category.

Stage 1: UniverseScreenerAgent (fast, rule-based, no LLM)
  → Reduces ~1700 NSE stocks to top 100 candidates by composite quant score

Stage 2: Full 9-agent research pipeline on each candidate (LLM-powered)
  → Produces complete research reports

Final: Rank by Buffett / Lynch / Fisher / Growth / SmallCap / Dividend / Risk
  → Return Top 10 per category

TODO: Add Screener.in API integration as primary financial data source.
TODO: Add Trendlyne API for institutional holding data and consensus estimates.
"""
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.agents.universe_screener import UniverseScreenerAgent
from src.agents.quarterly_earnings import QuarterlyEarningsAgent
from src.agents.orchestrator import Orchestrator
from src.agents.daily_report import (
    _score_buffett, _score_growth, _score_small_cap,
    _score_emerging_theme, _score_dividend, _score_fisher, _score_avoid,
    _pick_top,
)
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

def _score_lynch(report: Dict) -> float:
    """Peter Lynch: PEG < 1, consistent earnings growth, sector leadership."""
    peg = report.get("peg_ratio")
    peg_score = 0.0
    if peg is not None:
        if peg <= 0.5: peg_score = 10.0
        elif peg <= 1.0: peg_score = 8.0
        elif peg <= 1.5: peg_score = 5.0
        elif peg <= 2.0: peg_score = 2.0

    rev_cagr = (report.get("revenue_cagr_3y") or 0) * 100
    profit_cagr = (report.get("profit_cagr_3y") or 0) * 100
    eq_score = report.get("earnings_quality_score") or 5.0
    risk = report.get("risk_score") or 10

    return (peg_score * 0.35) + (rev_cagr * 0.20) + (profit_cagr * 0.20) + (eq_score * 0.15) + ((10 - risk) * 0.10)


def _pick_top10(reports: List[Dict], score_fn, reverse: bool = True, min_score: float = 0.0) -> List[Dict]:
    """Like _pick_top but returns 10 and includes earnings_quality_score in metrics."""
    scored = [(score_fn(r), r) for r in reports if r.get("final_rating") != "error"]
    scored.sort(key=lambda x: x[0], reverse=reverse)
    result = []
    for score, r in scored[:10]:
        if min_score and score < min_score:
            continue
        result.append({
            "ticker": r["ticker"],
            "name": r.get("name", r["ticker"]),
            "sector": r.get("sector", "—"),
            "final_rating": r.get("final_rating"),
            "category": r.get("category"),
            "score": round(score, 2),
            "current_price": r.get("current_price"),
            "market_cap_cr": r.get("market_cap_cr"),
            "key_metrics": {
                "roe_pct": round((r.get("roe") or 0) * 100, 1),
                "revenue_cagr_3y_pct": round((r.get("revenue_cagr_3y") or 0) * 100, 1),
                "profit_cagr_3y_pct": round((r.get("profit_cagr_3y") or 0) * 100, 1),
                "pe_ratio": r.get("pe_ratio"),
                "pb_ratio": r.get("pb_ratio"),
                "peg_ratio": r.get("peg_ratio"),
                "moat_score": r.get("moat_score"),
                "fisher_score": r.get("fisher_score"),
                "unicorn_score": r.get("unicorn_score"),
                "risk_score": r.get("risk_score"),
                "dividend_yield_pct": round((r.get("dividend_yield") or 0) * 100, 2),
                "earnings_quality_score": r.get("earnings_quality_score"),
                "emerging_themes": r.get("emerging_themes", []),
                "ten_x_potential": r.get("ten_x_potential"),
                "ten_x_candidate": r.get("ten_x_candidate"),
                "dcf_intrinsic_value": r.get("dcf_intrinsic_value"),
            },
            "synopsis": r.get("business_summary", "")[:300],
            "bull_case": r.get("bull_case", []),
            "bear_case": r.get("bear_case", []),
            "red_flags": [f.get("key") if isinstance(f, dict) else f for f in r.get("red_flags", [])],
            "moat_summary": r.get("moat_summary", "")[:200],
            "watch_triggers": r.get("watch_triggers", []),
        })
    return result


class UniverseScanOrchestrator:
    """
    Full NSE/BSE universe scanner.

    Usage:
        scanner = UniverseScanOrchestrator()
        result = scanner.run(max_candidates=50)  # runs Stage 1 + Stage 2
    """

    def __init__(self, config=None):
        self.cfg = config or get_config()
        self.screener = UniverseScreenerAgent(config=self.cfg)
        self.earnings_agent = QuarterlyEarningsAgent()
        self.orchestrator = Orchestrator(config=self.cfg)
        # Disclaimer text always comes from the real loaded config (see
        # fundamental_agent.py).
        self.disclaimer = get_config().disclaimer

    def run(
        self,
        symbol_list: Optional[List[str]] = None,
        stage1_top_n: int = 100,
        stage2_top_n: int = 50,
        progress_callback=None,
    ) -> Dict[str, Any]:
        """
        Run the full two-stage universe scan.

        Args:
            symbol_list: Optional override list of symbols. None = fetch from NSE API.
            stage1_top_n: How many candidates to pass from Stage 1 to Stage 2.
            stage2_top_n: How many of the Stage 1 candidates to run the full pipeline on.
                          Lower = faster and cheaper. Recommended: 30-50.
            progress_callback: Optional callable(stage, done, total, message) for UI updates.

        Returns:
            Full scan report with Top 10 per category.
        """
        start_time = datetime.utcnow()
        logger.info("=== Universe scan started ===")

        def _cb(stage, done, total, msg=""):
            if progress_callback:
                progress_callback(stage, done, total, msg)

        # ---------------------------------------------------------------
        # Stage 1: Quantitative screening
        # ---------------------------------------------------------------
        _cb("stage1", 0, 1, "Running quantitative pre-screen across NSE universe...")
        logger.info("Stage 1: quantitative screening")

        screen_result = self.screener.screen(
            symbol_list=symbol_list,
            top_n=stage1_top_n,
            progress_callback=lambda done, total: _cb("stage1", done, total, f"Screening {done}/{total}"),
        )

        candidates = screen_result["candidates"]
        stage2_candidates = candidates[:stage2_top_n]

        logger.info("Stage 1 complete: %d candidates → running Stage 2 on top %d",
                    len(candidates), len(stage2_candidates))
        _cb("stage2", 0, len(stage2_candidates), "Starting deep analysis...")

        # ---------------------------------------------------------------
        # Stage 2: Full 9-agent pipeline + quarterly earnings
        # ---------------------------------------------------------------
        reports = []
        for i, stock in enumerate(stage2_candidates):
            ticker = stock["ticker"]
            _cb("stage2", i + 1, len(stage2_candidates), f"Deep analysis: {ticker}")
            try:
                # Quarterly earnings (enriches the report)
                eq_data = self.earnings_agent.analyze(ticker)
                eq_score = eq_data.get("earnings_quality_score", 5.0)
                eq_trends = eq_data.get("trends", {})

                # Derive revenue/profit CAGR from quarterly trends if not available
                rev_cagr_approx = eq_trends.get("revenue_yoy_growth")
                profit_cagr_approx = eq_trends.get("profit_yoy_growth")

                # Build statements from screener data (yfinance doesn't give multi-year series,
                # so we use single-year approximation — Stage 2 will compute ratios from what's available)
                statements = []  # Full pipeline uses top-level fields

                # Run full research pipeline
                report = self.orchestrator.research(
                    ticker=ticker,
                    current_price=stock["current_price"],
                    market_cap_cr=stock["market_cap_cr"],
                    statements=statements,
                    business_description=stock.get("business_description") or f"{ticker} listed on NSE",
                    eps=stock.get("eps"),
                    book_value_per_share=stock.get("book_value_per_share"),
                    debt_cr=stock.get("debt_cr", 0.0),
                    cash_cr=stock.get("cash_cr", 0.0),
                    ebitda_cr=stock.get("ebitda_cr", 0.0),
                    fcf_cr=max(stock.get("fcf_cr", 0.0), 0.0),  # yfinance sometimes returns negative
                    shares_outstanding_cr=stock.get("shares_outstanding_cr", 1.0),
                    dividend_per_share=0.0,
                )

                # Enrich report with screener and earnings data
                report["name"] = stock.get("name", ticker)
                report["sector"] = stock.get("sector", "Unknown")
                report["industry"] = stock.get("industry", "Unknown")
                report["earnings_quality_score"] = eq_score
                report["revenue_yoy_growth"] = eq_trends.get("revenue_yoy_growth")
                report["profit_yoy_growth"] = eq_trends.get("profit_yoy_growth")
                report["margin_expanding"] = eq_trends.get("margin_expanding")
                report["earnings_accelerating"] = eq_trends.get("earnings_accelerating")

                # Override CAGR if fundamental agent got None (no multi-year statements)
                if report.get("revenue_cagr_3y") is None and rev_cagr_approx is not None:
                    report["revenue_cagr_3y"] = rev_cagr_approx
                if report.get("profit_cagr_3y") is None and profit_cagr_approx is not None:
                    report["profit_cagr_3y"] = profit_cagr_approx

                # Add screener quant scores as supplementary data
                report["buffett_quant_score"] = stock.get("buffett_quant_score")
                report["lynch_quant_score"] = stock.get("lynch_quant_score")

                reports.append(report)
                logger.info("Stage 2 complete for %s | rating=%s", ticker, report.get("final_rating"))

            except Exception as exc:
                logger.error("Stage 2 failed for %s: %s", ticker, exc)
                reports.append({
                    "ticker": ticker,
                    "name": stock.get("name", ticker),
                    "sector": stock.get("sector", "Unknown"),
                    "final_rating": "error",
                    "error": str(exc),
                })

        # ---------------------------------------------------------------
        # Ranking
        # ---------------------------------------------------------------
        _cb("ranking", 0, 1, "Ranking stocks across categories...")
        strong = [r for r in reports if r.get("final_rating") == "Strong Research Candidate"]
        watch = [r for r in reports if r.get("final_rating") == "Watch"]
        all_valid = strong + watch

        end_time = datetime.utcnow()
        duration_s = (end_time - start_time).total_seconds()

        scan_report = {
            "generated_at": start_time.isoformat() + "Z",
            "completed_at": end_time.isoformat() + "Z",
            "duration_seconds": round(duration_s, 1),
            "scan_stats": {
                "symbols_scanned": screen_result["total_symbols_scanned"],
                "passed_prefilter": screen_result["passed_prefilter"],
                "deep_analysed": len(stage2_candidates),
                "strong_candidates": len(strong),
                "watch_candidates": len(watch),
                "errors": sum(1 for r in reports if r.get("final_rating") == "error"),
            },
            # Top 10 per investment philosophy
            "top10_buffett": _pick_top10(all_valid, _score_buffett),
            "top10_lynch": _pick_top10(all_valid, _score_lynch),
            "top10_fisher": _pick_top10(all_valid, _score_fisher),
            "top10_growth": _pick_top10(all_valid, _score_growth),
            "top10_small_cap": _pick_top10(all_valid, _score_small_cap),
            "top10_emerging_themes": _pick_top10(all_valid, _score_emerging_theme),
            "top10_dividend": _pick_top10(all_valid, _score_dividend),
            "top10_avoid": _pick_top10(reports, _score_avoid, min_score=3.0),
            # Full reports for reference
            "all_reports_summary": [
                {
                    "ticker": r["ticker"],
                    "name": r.get("name", r["ticker"]),
                    "sector": r.get("sector", "—"),
                    "final_rating": r.get("final_rating"),
                    "risk_score": r.get("risk_score"),
                    "moat_score": r.get("moat_score"),
                    "fisher_score": r.get("fisher_score"),
                    "earnings_quality_score": r.get("earnings_quality_score"),
                }
                for r in reports
            ],
            "portfolio_rebalancing_note": (
                "Review top10_avoid against your existing holdings. "
                "Buffett picks: prioritise ROCE > 15% and moat score > 7. "
                "Lynch picks: validate PEG < 1 before entry. "
                "Fisher picks: research management track record before committing. "
                "Small cap picks carry higher risk — size positions accordingly."
            ),
            "data_sources": [
                "yfinance (NSE via Yahoo Finance)",
                "NewsAPI (if configured)",
                "Moneycontrol/ET/LiveMint RSS feeds",
                "Anthropic Claude LLM (if configured)",
            ],
            "data_source_note": (
                "TODO: Add Screener.in API for richer fundamental data. "
                "TODO: Add Trendlyne API for consensus estimates and institutional holding trends."
            ),
            "disclaimer": self.disclaimer,
        }

        logger.info(
            "=== Universe scan complete in %.0fs | %d strong | %d watch ===",
            duration_s, len(strong), len(watch),
        )
        return scan_report
