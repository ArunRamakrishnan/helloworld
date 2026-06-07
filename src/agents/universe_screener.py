"""Universe Screener Agent — Stage 1 fast rule-based filter across all NSE/BSE stocks.

Uses yfinance for financial data. No LLM calls — this is purely quantitative.
Reduces ~1700 NSE stocks → ~100-200 candidates for Stage 2 deep analysis.

TODO: Add Screener.in API as primary data source when API key is available.
TODO: Add Trendlyne API as secondary data source for richer fundamental data.
"""
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

# -----------------------------------------------------------------------
# Pre-screening filter thresholds
# -----------------------------------------------------------------------

MIN_MARKET_CAP_CR = 100          # Filter out micro-caps with no liquidity
MAX_MARKET_CAP_CR = 10_000_000   # No upper cap (large caps are valid too)
MIN_PRICE_INR = 5                # Filter true penny stocks
MIN_ROE = 0.06                   # At least 6% ROE
MAX_DEBT_EQUITY = 4.0            # Debt/Equity ceiling (banks exempted by sector)
MIN_REVENUE_CR = 50              # Must have meaningful revenue
MAX_WORKERS = 12                 # Parallel yfinance fetch threads

# INR conversion: yfinance returns values in native currency (INR for NSE)
# Market cap is in INR units from yfinance — divide by 1e7 to get crores
INR_TO_CR = 1e7

# -----------------------------------------------------------------------
# Fallback static NSE symbol list (used when NSE API is unavailable)
# Covers NIFTY 100 + popular mid/small caps across sectors
# -----------------------------------------------------------------------

NIFTY100_FALLBACK = [
    # Large cap
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR", "ICICIBANK", "KOTAKBANK",
    "BHARTIARTL", "ITC", "AXISBANK", "BAJFINANCE", "ASIANPAINT", "MARUTI", "TITAN",
    "SUNPHARMA", "WIPRO", "ULTRACEMCO", "NESTLEIND", "TECHM", "POWERGRID",
    "NTPC", "ONGC", "COALINDIA", "JSWSTEEL", "TATAMOTORS", "TATASTEEL",
    "HCLTECH", "LT", "SBILIFE", "HDFCLIFE",
    # Mid cap growth
    "DIXON", "AMBER", "KAYNES", "WAAREEENER", "SUZLON", "IRFC", "HAL",
    "BHEL", "BEL", "COCHINSHIP", "GRSE", "MAZAGON", "PARAS", "CDSL",
    "BSOFT", "MPHASIS", "COFORGE", "PERSISTENT", "LTTS",
    # Small cap / emerging
    "IDEAFORGE", "SYRMA", "AVALON", "ELIN", "IFCI", "RVNL", "IRCON",
    "RAILTEL", "NMDC", "MOIL", "NATIONALUM", "HINDZINC",
    # Banking / NBFC
    "BANDHANBNK", "IDFCFIRSTB", "RBLBANK", "FEDERALBNK", "INDUSINDBK",
    "CHOLAFIN", "BAJAJFINSV", "MUTHOOTFIN", "MANAPPURAM",
    # Consumer / FMCG
    "DABUR", "MARICO", "GODREJCP", "COLPAL", "EMAMILTD", "VBL", "TATACONSUM",
    # Pharma / Healthcare
    "DRREDDY", "CIPLA", "LUPIN", "BIOCON", "AUROPHARMA", "ALKEM", "TORNTPHARM",
    "DIVISLAB", "GLAND", "METROPOLIS", "THYROCARE",
    # Specialty chemicals
    "PIDILITIND", "AAVAS", "FINPIPE", "ALKYLAMINE", "GALAXYSURF",
    "CLEAN", "ATUL", "NAVINFLUOR",
    # Infra / Capex
    "ADANIGREEN", "ADANIPORTS", "ADANIENT", "TATAPOWER", "CESC",
    "TORNTPOWER", "JSPL", "HINDALCO",
]


class UniverseScreenerAgent:
    """
    Stage 1: Fast quantitative screener across NSE universe.

    Flow:
    1. Fetch stock list (NSE API → fallback static list)
    2. Parallel yfinance fetch for each stock's key financials
    3. Apply hard pre-filters
    4. Score survivors on Buffett / Lynch / Fisher / Risk dimensions
    5. Return ranked candidates with financial data ready for Stage 2
    """

    def __init__(self, config=None, max_stocks: int = 500):
        self.cfg = config or get_config()
        self.max_stocks = max_stocks  # cap for testing / cost control

    # -----------------------------------------------------------------------
    # Symbol list
    # -----------------------------------------------------------------------

    def get_symbol_list(self) -> List[str]:
        """Return list of NSE symbols to screen. Uses fallback if API unavailable."""
        try:
            from src.agents.data_collector import DataCollectorAgent
            collector = DataCollectorAgent(config=self.cfg)
            stocks = collector.fetch_nse_stock_list()
            collector.close()
            if stocks:
                symbols = [s["ticker"] for s in stocks if s.get("ticker")]
                logger.info("Fetched %d symbols from NSE API", len(symbols))
                return symbols[: self.max_stocks]
        except Exception as exc:
            logger.warning("NSE API failed (%s) — using fallback symbol list", exc)
        return NIFTY100_FALLBACK[: self.max_stocks]

    # -----------------------------------------------------------------------
    # yfinance fetch (one stock at a time — called in parallel)
    # -----------------------------------------------------------------------

    def _fetch_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch yfinance info dict for one NSE symbol. Returns None on failure."""
        try:
            import yfinance as yf
            ticker = yf.Ticker(f"{symbol}.NS")
            info = ticker.info
            if not info or info.get("regularMarketPrice") is None:
                return None
            return info
        except Exception as exc:
            logger.debug("yfinance fetch failed for %s: %s", symbol, exc)
            return None

    def _parse_info(self, symbol: str, info: Dict[str, Any]) -> Dict[str, Any]:
        """Parse yfinance info dict into standardised financial fields."""
        mcap_raw = info.get("marketCap") or 0
        mcap_cr = mcap_raw / INR_TO_CR

        revenue_raw = info.get("totalRevenue") or 0
        revenue_cr = revenue_raw / INR_TO_CR

        fcf_raw = info.get("freeCashflow") or 0
        fcf_cr = fcf_raw / INR_TO_CR

        debt_raw = info.get("totalDebt") or 0
        debt_cr = debt_raw / INR_TO_CR

        cash_raw = info.get("totalCash") or 0
        cash_cr = cash_raw / INR_TO_CR

        return {
            "ticker": symbol,
            "name": info.get("longName") or info.get("shortName") or symbol,
            "sector": info.get("sector") or "Unknown",
            "industry": info.get("industry") or "Unknown",
            "current_price": info.get("regularMarketPrice") or info.get("currentPrice") or 0,
            "market_cap_cr": round(mcap_cr, 2),
            "revenue_cr": round(revenue_cr, 2),
            "fcf_cr": round(fcf_cr, 2),
            "debt_cr": round(debt_cr, 2),
            "cash_cr": round(cash_cr, 2),
            "roe": info.get("returnOnEquity"),
            "roa": info.get("returnOnAssets"),
            # yfinance reports debtToEquity as a percentage (e.g. 42 means 0.42)
            "debt_equity": (info["debtToEquity"] / 100) if info.get("debtToEquity") is not None else None,
            "pe_ratio": info.get("trailingPE"),
            "pb_ratio": info.get("priceToBook"),
            "peg_ratio": info.get("pegRatio"),
            "eps": info.get("trailingEps"),
            "book_value_per_share": info.get("bookValue"),
            "dividend_yield": info.get("dividendYield"),
            "revenue_growth_yoy": info.get("revenueGrowth"),
            "earnings_growth_yoy": info.get("earningsGrowth"),
            "gross_margin": info.get("grossMargins"),
            "operating_margin": info.get("operatingMargins"),
            "profit_margin": info.get("profitMargins"),
            "current_ratio": info.get("currentRatio"),
            "ebitda_cr": round((info.get("ebitda") or 0) / INR_TO_CR, 2),
            "shares_outstanding_cr": round((info.get("sharesOutstanding") or 0) / INR_TO_CR, 4),
            "business_description": (info.get("longBusinessSummary") or "")[:500],
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "beta": info.get("beta"),
            "exchange": "NSE",
        }

    # -----------------------------------------------------------------------
    # Pre-filters
    # -----------------------------------------------------------------------

    def _passes_prefilter(self, stock: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Returns (passes, reason_if_rejected).
        Hard filters — any failure eliminates the stock.
        """
        if stock["market_cap_cr"] < MIN_MARKET_CAP_CR:
            return False, f"market_cap_cr={stock['market_cap_cr']:.0f} < {MIN_MARKET_CAP_CR}"

        if stock["current_price"] < MIN_PRICE_INR:
            return False, f"price={stock['current_price']} < {MIN_PRICE_INR}"

        if stock["revenue_cr"] < MIN_REVENUE_CR:
            return False, f"revenue_cr={stock['revenue_cr']:.0f} < {MIN_REVENUE_CR}"

        roe = stock.get("roe")
        if roe is not None and roe < MIN_ROE:
            return False, f"roe={roe:.2f} < {MIN_ROE}"

        de = stock.get("debt_equity")
        sector = stock.get("sector", "").lower()
        de_limit = MAX_DEBT_EQUITY * 3 if "financial" in sector else MAX_DEBT_EQUITY
        if de is not None and de > de_limit:
            return False, f"debt_equity={de:.1f} > {de_limit}"

        if not stock.get("business_description"):
            return False, "no business description"

        return True, ""

    # -----------------------------------------------------------------------
    # Quantitative scoring (no LLM)
    # -----------------------------------------------------------------------

    def _quant_score(self, stock: Dict[str, Any]) -> Dict[str, float]:
        """Score a stock on Buffett / Lynch / Fisher / Risk dimensions using only numbers."""

        roe = stock.get("roe") or 0
        de = stock.get("debt_equity") or 0
        rev_growth = stock.get("revenue_growth_yoy") or 0
        earn_growth = stock.get("earnings_growth_yoy") or 0
        peg = stock.get("peg_ratio")
        margin = stock.get("profit_margin") or 0
        op_margin = stock.get("operating_margin") or 0
        fcf = stock.get("fcf_cr") or 0
        mcap = stock.get("market_cap_cr") or 0
        div_yield = stock.get("dividend_yield") or 0
        beta = stock.get("beta") or 1.0

        # --- Buffett score ---
        buffett = 0.0
        if roe >= 0.25: buffett += 3.0
        elif roe >= 0.15: buffett += 2.0
        elif roe >= 0.10: buffett += 1.0

        if de <= 0.3: buffett += 2.5
        elif de <= 0.7: buffett += 1.5
        elif de <= 1.5: buffett += 0.5

        if fcf > 0: buffett += 2.0
        if margin >= 0.20: buffett += 1.5
        elif margin >= 0.10: buffett += 0.5

        buffett = min(10.0, buffett)

        # --- Lynch score (growth at reasonable price) ---
        lynch = 0.0
        if rev_growth >= 0.25: lynch += 3.0
        elif rev_growth >= 0.15: lynch += 2.0
        elif rev_growth >= 0.08: lynch += 1.0

        if earn_growth >= 0.25: lynch += 2.5
        elif earn_growth >= 0.15: lynch += 1.5
        elif earn_growth >= 0.08: lynch += 0.5

        if peg is not None:
            if peg <= 0.5: lynch += 3.0
            elif peg <= 1.0: lynch += 2.0
            elif peg <= 1.5: lynch += 1.0

        lynch = min(10.0, lynch)

        # --- Fisher score (qualitative proxy via margins + growth) ---
        fisher = 0.0
        if op_margin >= 0.25: fisher += 3.0
        elif op_margin >= 0.15: fisher += 2.0
        elif op_margin >= 0.08: fisher += 1.0

        if rev_growth >= 0.30: fisher += 3.0
        elif rev_growth >= 0.20: fisher += 2.0
        elif rev_growth >= 0.10: fisher += 1.0

        if earn_growth >= 0.30: fisher += 2.0
        elif earn_growth >= 0.20: fisher += 1.5
        elif earn_growth >= 0.10: fisher += 0.5

        # Small/mid cap bonus for Fisher (more room to grow)
        if mcap <= 5000: fisher += 1.5
        elif mcap <= 20000: fisher += 0.5

        fisher = min(10.0, fisher)

        # --- Risk score (lower = safer) ---
        risk = 0.0
        if de > 2.0: risk += 2.0
        elif de > 1.0: risk += 1.0
        if fcf < 0: risk += 2.0
        if beta and beta > 1.5: risk += 1.0
        if de > 3.0: risk += 1.5

        risk = min(10.0, risk)

        # --- Dividend score ---
        dividend = 0.0
        if div_yield and div_yield >= 0.04: dividend += 4.0
        elif div_yield and div_yield >= 0.02: dividend += 2.0
        if roe >= 0.15 and de <= 1.0: dividend += 3.0
        elif roe >= 0.10: dividend += 1.5
        if fcf > 0: dividend += 2.0
        dividend = min(10.0, dividend)

        # --- Composite screen score ---
        composite = (buffett * 0.3) + (lynch * 0.25) + (fisher * 0.2) + ((10 - risk) * 0.15) + (dividend * 0.1)

        return {
            "buffett_quant_score": round(buffett, 2),
            "lynch_quant_score": round(lynch, 2),
            "fisher_quant_score": round(fisher, 2),
            "risk_quant_score": round(risk, 2),
            "dividend_quant_score": round(dividend, 2),
            "composite_screen_score": round(composite, 2),
        }

    # -----------------------------------------------------------------------
    # Main entry
    # -----------------------------------------------------------------------

    def screen(
        self,
        symbol_list: Optional[List[str]] = None,
        top_n: int = 100,
        progress_callback=None,
    ) -> Dict[str, Any]:
        """
        Run full universe screen.

        Args:
            symbol_list: Override list of symbols. If None, fetches from NSE API.
            top_n: Return top N candidates after filtering.
            progress_callback: Optional callable(done, total) for progress updates.

        Returns:
            Dict with candidates list and screening stats.
        """
        symbols = symbol_list or self.get_symbol_list()
        total = len(symbols)
        logger.info("Starting universe screen on %d symbols", total)

        raw_results: List[Dict] = []
        rejected_count = 0
        fetch_failed = 0

        # Parallel fetch
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
            futures = {pool.submit(self._fetch_stock_info, sym): sym for sym in symbols}
            done = 0
            for future in as_completed(futures):
                sym = futures[future]
                done += 1
                if progress_callback:
                    progress_callback(done, total)
                try:
                    info = future.result()
                    if info is None:
                        fetch_failed += 1
                        continue
                    stock = self._parse_info(sym, info)
                    passes, reason = self._passes_prefilter(stock)
                    if not passes:
                        rejected_count += 1
                        logger.debug("Filtered out %s: %s", sym, reason)
                        continue
                    scores = self._quant_score(stock)
                    stock.update(scores)
                    raw_results.append(stock)
                except Exception as exc:
                    logger.error("Error processing %s: %s", sym, exc)
                    fetch_failed += 1

        # Sort by composite score and take top N
        raw_results.sort(key=lambda x: x.get("composite_screen_score", 0), reverse=True)
        candidates = raw_results[:top_n]

        logger.info(
            "Screen complete: %d total, %d passed filters, %d fetch failures, %d returned",
            total, len(raw_results), fetch_failed, len(candidates),
        )

        return {
            "total_symbols_scanned": total,
            "passed_prefilter": len(raw_results),
            "fetch_failures": fetch_failed,
            "rejected_by_filter": rejected_count,
            "candidates_returned": len(candidates),
            "candidates": candidates,
        }
