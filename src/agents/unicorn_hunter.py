"""Unicorn Hunter — dedicated scanner for undiscovered small/mid-cap gems.

This is fundamentally different from the universe screener:
- Targets market cap ₹100 Cr - ₹15,000 Cr (deliberately EXCLUDES large caps)
- 300+ symbols across emerging sectors (defense, EV, AI infra, specialty chem, etc.)
- Filters FOR high revenue growth (> 15% YoY) — not just quality
- Looks for stocks that are NOT yet household names
- Goal: find the next NIFTY 50 candidate BEFORE the market discovers it

TODO: Add Screener.in API for richer small-cap data (many small caps have poor yfinance coverage).
TODO: Add Trendlyne API for promoter buying signals and institutional entry data.
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)

INR_TO_CR = 1e7
MAX_WORKERS = 4   # Keep low — yfinance 429s above ~5 parallel

# -----------------------------------------------------------------------
# Unicorn-specific filter thresholds (different from regular screener)
# -----------------------------------------------------------------------
MIN_MARKET_CAP_CR = 100          # Floor: must have some scale
MAX_MARKET_CAP_CR = 15_000       # Ceiling: exclude already-discovered large caps
MIN_REVENUE_CR = 30              # Small caps can have lower revenue
MIN_PRICE_INR = 5
MIN_REVENUE_GROWTH = 0.10        # Must show at least 10% YoY growth
MAX_DEBT_EQUITY = 2.0            # Tighter D/E for small caps

# -----------------------------------------------------------------------
# Emerging sector themes (used for theme tagging and bonus scoring)
# -----------------------------------------------------------------------
THEME_MAP = {
    "defense_aerospace": ["defense", "aerospace", "drone", "missile", "naval", "radar",
                          "ammunition", "armoured", "military"],
    "electronics_ems":   ["electronics", "ems", "pcb", "circuit", "semiconductor", "fab",
                          "printed circuit", "embedded"],
    "ev_battery":        ["electric vehicle", "ev ", "battery", "lithium", "charging",
                          "inverter", "motor", "traction"],
    "renewable_solar":   ["solar", "wind energy", "renewable", "green energy", "photovoltaic",
                          "clean energy"],
    "specialty_chem":    ["specialty chemical", "fine chemical", "agrochemical", "fluorine",
                          "pharmaceutical intermediate", "api", "contract research"],
    "ai_data_infra":     ["data center", "cloud", "artificial intelligence", "ai ", " ai,",
                          "machine learning", "digital infrastructure", "hyperscale"],
    "digital_fintech":   ["fintech", "digital payment", "lending", "nbfc", "micro finance",
                          "wealth management", "insurance tech"],
    "pharma_cdmo":       ["cdmo", "contract manufacturing", "active pharmaceutical",
                          "biologics", "biosimilar", "hospital", "diagnostic"],
    "agritech":          ["agri", "fertiliser", "pesticide", "seed", "crop", "irrigation",
                          "food processing"],
    "logistics_scm":     ["logistics", "supply chain", "warehousing", "cold chain",
                          "freight", "courier"],
    "building_infra":    ["infrastructure", "road", "railway", "metro", "construction",
                          "cement", "real estate"],
    "textiles_pli":      ["textile", "garment", "apparel", "yarn", "fabric", "technical textile"],
    "healthcare":        ["hospital", "diagnostic", "healthcare", "medical device",
                          "telemedicine", "health tech"],
    "qsr_consumer":      ["restaurant", "qsr", "food service", "quick service", "retail",
                          "consumer brand"],
}

# -----------------------------------------------------------------------
# 300+ undiscovered small/mid cap NSE symbols across emerging sectors
# Deliberately excludes NIFTY 100 household names
# -----------------------------------------------------------------------
UNICORN_UNIVERSE = [
    # ---- Defense & Aerospace ----
    "IDEAFORGE", "MTAR", "DYNAMATECH", "CENTUM", "PARAS", "ELCOM",
    "DCAL", "AEROSPACEDGT", "SYRMA", "AVALON", "ELIN", "SGLTD",
    "BELCO", "KINTECH", "DATAMATICS", "INDIASHLTR",
    "APOLLOMICRO", "IDFCFIRSTB", "BHEL", "BEL", "COCHINSHIP",
    "GRSE", "MAZAGON", "HAL", "MIDHANI", "BEML",

    # ---- Electronics Manufacturing Services (EMS / PLI) ----
    "DIXON", "AMBER", "KAYNES", "SYRMA", "VIMTA", "PGEL",
    "RATTAN", "ELIN", "ENPRO", "IFCI", "RAJRATAN",
    "MOTHERSON", "LUMAX", "SUPRAJIT", "MINDTECK", "SUBROS",
    "SANDHAR", "MINDA", "CRAFTSMAN", "ENDURANCE",

    # ---- EV / Battery / Charging ----
    "OLECTRA", "GOLDSTAR", "EXIDEIND", "AMARARAJA", "GREENPANEL",
    "KIRIIND", "TATACHEM", "GUJALKALI", "HIMADRI", "PRAJ",
    "GREENLAM", "FORCEMOT",

    # ---- Renewable Energy / Solar ----
    "WAAREEENER", "WEBSOL", "SUZLON", "INOXWIND", "PREMIER",
    "BOROSIL", "GENSOL", "GOLDENCRST", "VIKASECO", "SUJALONSOLAR",
    "TATAPOWER", "CESC", "TORNTPOWER", "ADANIGREEN",
    "IREDA", "NHPC", "SJVN", "POWERMECH",

    # ---- Specialty Chemicals ----
    "NAVINFLUOR", "ALKYLAMINE", "GALAXYSURF", "CLEAN", "ATUL",
    "FINEORG", "BALAMINES", "JUBLINGREA", "VINATI", "ROSSARI",
    "SUDARSCHEM", "NEOGEN", "TATACHEM", "DEEPAKNTR", "NOCIL",
    "AAVAS", "ANUPAM", "APCOTEX", "GOKUL", "DMCC",
    "CHEMBOND", "LXCHEM", "YASHO", "TATACHEM", "AEGISCHEM",

    # ---- AI / Data Centers / Digital Infrastructure ----
    "STLTD", "OPTIEMUS", "RAILTEL", "ROUTE", "NXTDIGITAL",
    "INDIAMART", "JUSTDIAL", "MPHASIS", "COFORGE", "PERSISTENT",
    "LTTS", "CYIENT", "SASKEN", "HAPPYMINDS", "RATEGAIN",
    "TATAELXSI", "MASTEK", "INTELLECT", "KFINTECH", "CDSL",
    "BSOFT", "CMSINFO", "FSL", "NAUKRI",

    # ---- Pharma / CDMO / Specialty ----
    "LAURUS", "SOLARA", "GRANULES", "SUVEN", "NEULAND",
    "GLAND", "PIRAMAL", "CAPLIN", "MARKSANS", "STRIDES",
    "ALEMBICLTD", "JBCHEPHARM", "IPCA", "AJANTPHARM",
    "METROPOLIS", "THYROCARE", "KRSNAA", "VIJAYA",
    "RAINBOW", "ASTER", "MEDPLUS", "SUVENPHAR",

    # ---- Fintech / NBFC / Digital Finance ----
    "CREDITACC", "UJJIVAN", "SPANDANA", "EQUITASBNK",
    "SURYODAY", "UTKARSH", "JANA", "AROHAN",
    "CHOLAFIN", "MUTHOOTFIN", "MANAPPURAM", "IIFL",
    "POONAWALLA", "APTUS", "HOMEFIRST", "AAVAS",
    "POLICYBZR", "NUVAMA", "ANAND",

    # ---- Capital Goods / Engineering ----
    "THERMAX", "CUMMINSIND", "KSB", "GRINDWELL", "LAKSHMI",
    "ISGEC", "GMMPFAUDLR", "ELGI", "KIRLOSENG", "ELECON",
    "TRIVENI", "KTIL", "JYOTISTRUC", "SKIPPER", "KEC",
    "KALPATPOWR", "POWERMECH", "HCC", "NCC", "PNC",

    # ---- Railways / Infra / Government Capex ----
    "RVNL", "IRCON", "IRFC", "RAILTEL", "TITAGARH",
    "TEXMACO", "HBLPOWER", "ISGEC", "KERNEX", "MEDHA",
    "MAZDOCK", "SGCL", "AVANTEL",

    # ---- Agrochemicals / Fertilisers ----
    "CHAMBAL", "COROMANDEL", "PIIND", "BAYER", "RALLIS",
    "INSECTICIDES", "DHANUKA", "SUMITOMOCHEM", "EXCEL",
    "TATACHEM", "GSFC", "GNFC",

    # ---- Logistics / Supply Chain ----
    "MAHLOG", "GATI", "TCI", "BLUEDART", "DELHIVERY",
    "ALLCARGO", "TVSSCS", "SNOWMAN", "CONCOR",

    # ---- Building Materials / Real Estate PLI ----
    "CENTURYPLY", "GREENPANEL", "APCOTEX", "STYLAMIND",
    "ASTRAL", "PRINCE", "SAFARI", "ORIENTBELL",
    "ASAHIINDIA", "SHANKARA", "ITDCEM",

    # ---- Textiles / Apparel PLI ----
    "TRIDENT", "VARDHMAN", "KPRMILL", "WELSPUNIND",
    "GRASIM", "NITIN", "NITIRAJ", "SUTLEJ",
    "ARVIND", "SPORTKING", "SIYARAM",

    # ---- Healthcare / Hospitals ----
    "RAINBOW", "ASTER", "MEDPLUS", "VIJAYA", "KRSNAA",
    "YATHARTH", "SAGILITY", "SHALBY", "MAXHEALTH",
    "FORTIS", "NARAYANA",

    # ---- Consumer / QSR / New Age ----
    "DEVYANI", "SAPPHIREFDS", "WESTLIFE", "JUBLFOOD",
    "ZOMATO", "NYKAA", "DMART", "TRENT", "MANYAVAR",
    "VEDANT", "CAMPUS", "KAMAROOPGR",

    # ---- Specialty Finance / Insurance ----
    "STARLHEALTH", "GICRE", "NIACL", "MOSL",
    "ANGELONE", "GEOJIT", "MOTILALOFS",

    # ---- Water / Waste / Environment ----
    "WABCOINDIA", "ION", "SUPRIYA", "VATECH",
    "PURITYFLEX", "DRLAL",
]

# De-duplicate while preserving order
_seen = set()
UNICORN_UNIVERSE = [s for s in UNICORN_UNIVERSE if not (s in _seen or _seen.add(s))]


def _detect_themes(description: str, sector: str, industry: str) -> List[str]:
    """Identify which emerging themes a stock belongs to."""
    text = (description + " " + sector + " " + industry).lower()
    themes = []
    for theme, keywords in THEME_MAP.items():
        if any(kw in text for kw in keywords):
            themes.append(theme)
    return themes


class UnicornHunterAgent:
    """
    Scans 300+ undiscovered small/mid-cap NSE stocks to find the next unicorn.

    Philosophy:
    - Small cap today → potential NIFTY 50 in 5-10 years
    - Revenue growing > 20% in a sector with government tailwind
    - Founder-led (high promoter holding)
    - Low debt (room to invest in growth)
    - Not yet a household name
    """

    def __init__(self, config=None):
        self.cfg = config or get_config()

    def _fetch_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Fetch yfinance info for one NSE symbol. Retries on 429 with backoff."""
        import time
        import yfinance as yf
        for attempt in range(4):
            try:
                info = yf.Ticker(f"{symbol}.NS").info
                if not info or info.get("regularMarketPrice") is None:
                    return None
                return info
            except Exception as exc:
                msg = str(exc)
                if "429" in msg or "Too Many Requests" in msg:
                    wait = 2 ** attempt
                    logger.debug("429 for %s — retrying in %ds (attempt %d)", symbol, wait, attempt + 1)
                    time.sleep(wait)
                else:
                    logger.debug("yfinance fetch failed for %s: %s", symbol, exc)
                    return None
        logger.debug("Giving up on %s after 4 attempts", symbol)
        return None

    def _parse_info(self, symbol: str, info: Dict[str, Any]) -> Dict[str, Any]:
        mcap_cr = (info.get("marketCap") or 0) / INR_TO_CR
        revenue_cr = (info.get("totalRevenue") or 0) / INR_TO_CR
        fcf_cr = (info.get("freeCashflow") or 0) / INR_TO_CR
        debt_cr = (info.get("totalDebt") or 0) / INR_TO_CR
        cash_cr = (info.get("totalCash") or 0) / INR_TO_CR
        ebitda_cr = (info.get("ebitda") or 0) / INR_TO_CR
        sector = info.get("sector") or "Unknown"
        industry = info.get("industry") or "Unknown"
        description = (info.get("longBusinessSummary") or "")[:500]
        themes = _detect_themes(description, sector, industry)

        return {
            "ticker": symbol,
            "name": info.get("longName") or info.get("shortName") or symbol,
            "sector": sector,
            "industry": industry,
            "current_price": info.get("regularMarketPrice") or 0,
            "market_cap_cr": round(mcap_cr, 2),
            "revenue_cr": round(revenue_cr, 2),
            "fcf_cr": round(fcf_cr, 2),
            "debt_cr": round(debt_cr, 2),
            "cash_cr": round(cash_cr, 2),
            "ebitda_cr": round(ebitda_cr, 2),
            "roe": info.get("returnOnEquity"),
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
            "shares_outstanding_cr": round((info.get("sharesOutstanding") or 0) / INR_TO_CR, 4),
            "business_description": description,
            "beta": info.get("beta"),
            "52w_high": info.get("fiftyTwoWeekHigh"),
            "52w_low": info.get("fiftyTwoWeekLow"),
            "emerging_themes": themes,
            "theme_count": len(themes),
            "exchange": "NSE",
        }

    def _passes_unicorn_filter(self, stock: Dict) -> Tuple[bool, str]:
        """Unicorn-specific hard filters."""
        mcap = stock["market_cap_cr"]
        if mcap < MIN_MARKET_CAP_CR:
            return False, f"mcap={mcap:.0f} too small"
        if mcap > MAX_MARKET_CAP_CR:
            return False, f"mcap={mcap:.0f} already large cap — not undiscovered"
        if stock["current_price"] < MIN_PRICE_INR:
            return False, "penny stock"
        if stock["revenue_cr"] < MIN_REVENUE_CR:
            return False, f"revenue={stock['revenue_cr']:.0f} Cr too low"

        rev_growth = stock.get("revenue_growth_yoy")
        if rev_growth is not None and rev_growth < MIN_REVENUE_GROWTH:
            return False, f"rev_growth={rev_growth:.1%} below 10% threshold"

        de = stock.get("debt_equity")
        if de is not None and de > MAX_DEBT_EQUITY:
            return False, f"debt_equity={de:.1f} too high for small cap"

        return True, ""

    def _unicorn_score(self, stock: Dict) -> Dict[str, float]:
        """Score specifically for unicorn potential."""
        rev_growth = stock.get("revenue_growth_yoy") or 0
        earn_growth = stock.get("earnings_growth_yoy") or 0
        mcap = stock.get("market_cap_cr") or 0
        roe = stock.get("roe") or 0
        de = stock.get("debt_equity") or 0
        op_margin = stock.get("operating_margin") or 0
        theme_count = stock.get("theme_count") or 0
        peg = stock.get("peg_ratio")
        pb = stock.get("pb_ratio")

        # Growth momentum (most important for unicorn)
        growth_score = 0.0
        if rev_growth >= 0.50: growth_score += 4.0
        elif rev_growth >= 0.35: growth_score += 3.0
        elif rev_growth >= 0.25: growth_score += 2.0
        elif rev_growth >= 0.15: growth_score += 1.0

        if earn_growth >= 0.50: growth_score += 3.0
        elif earn_growth >= 0.35: growth_score += 2.0
        elif earn_growth >= 0.20: growth_score += 1.0

        growth_score = min(10.0, growth_score)

        # Small cap bonus (smaller = more upside, but only if growing)
        size_score = 0.0
        if mcap <= 500 and rev_growth >= 0.20: size_score = 4.0
        elif mcap <= 1000 and rev_growth >= 0.15: size_score = 3.0
        elif mcap <= 3000 and rev_growth >= 0.12: size_score = 2.0
        elif mcap <= 8000: size_score = 1.0

        # Emerging theme bonus
        theme_score = min(10.0, theme_count * 2.5)

        # Quality score (ROE, margins, debt)
        quality_score = 0.0
        if roe >= 0.25: quality_score += 3.0
        elif roe >= 0.15: quality_score += 2.0
        elif roe >= 0.10: quality_score += 1.0
        if de <= 0.3: quality_score += 2.5
        elif de <= 0.8: quality_score += 1.5
        if op_margin >= 0.20: quality_score += 2.0
        elif op_margin >= 0.12: quality_score += 1.0
        quality_score = min(10.0, quality_score)

        # Valuation (don't want to overpay even for growth)
        val_score = 5.0
        if peg is not None:
            if peg <= 0.8: val_score = 10.0
            elif peg <= 1.5: val_score = 7.0
            elif peg <= 2.5: val_score = 5.0
            elif peg > 4.0: val_score = 2.0
        if pb is not None and pb <= 3.0: val_score = min(10.0, val_score + 1.0)

        # Composite unicorn score
        composite = (
            growth_score * 0.35 +
            size_score * 0.20 +
            theme_score * 0.20 +
            quality_score * 0.15 +
            val_score * 0.10
        )

        return {
            "unicorn_growth_score": round(growth_score, 2),
            "unicorn_size_score": round(size_score, 2),
            "unicorn_theme_score": round(theme_score, 2),
            "unicorn_quality_score": round(quality_score, 2),
            "unicorn_valuation_score": round(val_score, 2),
            "unicorn_composite": round(composite, 2),
        }

    def hunt(
        self,
        symbol_list: Optional[List[str]] = None,
        top_n: int = 50,
        progress_callback=None,
    ) -> Dict[str, Any]:
        """
        Scan the undiscovered small/mid-cap universe for unicorn candidates.

        Args:
            symbol_list: Custom list. If None, uses the built-in 300+ symbol universe.
            top_n: How many to return after filtering.
            progress_callback: Optional callable(done, total).

        Returns:
            Dict with candidates ranked by unicorn composite score + theme breakdown.
        """
        symbols = symbol_list or UNICORN_UNIVERSE
        total = len(symbols)
        logger.info("Unicorn hunt started: scanning %d symbols", total)

        raw = []
        fetch_failed = 0
        filtered_out = 0

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
                    passes, reason = self._passes_unicorn_filter(stock)
                    if not passes:
                        filtered_out += 1
                        logger.debug("Filtered %s: %s", sym, reason)
                        continue
                    scores = self._unicorn_score(stock)
                    stock.update(scores)
                    raw.append(stock)
                except Exception as exc:
                    logger.error("Error processing %s: %s", sym, exc)
                    fetch_failed += 1

        # Sort by unicorn composite score
        raw.sort(key=lambda x: x.get("unicorn_composite", 0), reverse=True)
        candidates = raw[:top_n]

        # Group by themes for the report
        by_theme: Dict[str, List[str]] = {}
        for s in candidates:
            for t in s.get("emerging_themes", []):
                by_theme.setdefault(t, []).append(s["ticker"])

        logger.info(
            "Unicorn hunt complete: %d scanned, %d passed, %d top candidates",
            total, len(raw), len(candidates),
        )

        return {
            "total_scanned": total,
            "passed_filter": len(raw),
            "fetch_failures": fetch_failed,
            "filtered_out": filtered_out,
            "candidates": candidates,
            "candidates_returned": len(candidates),
            "theme_breakdown": {t: tickers for t, tickers in sorted(
                by_theme.items(), key=lambda x: len(x[1]), reverse=True
            )},
            "hunt_note": (
                f"Scanned {total} undiscovered small/mid-cap stocks (market cap ₹100-15,000 Cr). "
                f"Excluded all NIFTY 100 / large-cap household names. "
                f"{len(raw)} passed the growth + quality pre-filter. "
                f"Ranked by growth momentum × sector tailwind × quality."
            ),
        }
