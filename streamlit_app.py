"""Indian Investment Research Wizard — Streamlit Dashboard."""
import json
import time
from typing import Any, Dict, List

import streamlit as st

from src.agents.orchestrator import Orchestrator
from src.agents.daily_report import DailyReportOrchestrator
from src.agents.universe_scan import UniverseScanOrchestrator
from src.agents.universe_screener import NIFTY100_FALLBACK
from src.utils.config import get_config

st.set_page_config(
    page_title="Indian Investment Research Wizard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

DISCLAIMER = (
    "⚠️ **Disclaimer:** This is educational research, not financial advice. "
    "Consult a SEBI-registered investment adviser before investing."
)

SCORE_COLORS = {
    "Strong Research Candidate": "🟢",
    "Watch": "🟡",
    "Avoid": "🔴",
}

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

@st.cache_resource
def get_orchestrator():
    return Orchestrator(config=get_config())


@st.cache_resource
def get_daily_orchestrator():
    return DailyReportOrchestrator(config=get_config())


def pct(val):
    if val is None:
        return "—"
    return f"{val * 100:.1f}%"


def fmt(val, decimals=2):
    if val is None:
        return "—"
    return f"{val:.{decimals}f}"


def score_bar(score, max_val=10):
    if score is None:
        return "—"
    filled = int(round(score / max_val * 10))
    bar = "█" * filled + "░" * (10 - filled)
    return f"{bar} {score:.1f}/10"


def rating_badge(rating):
    return SCORE_COLORS.get(rating, "⚪") + " " + (rating or "—")


# ------------------------------------------------------------------
# Pages
# ------------------------------------------------------------------

def page_single_stock():
    st.header("🔍 Single Stock Research")
    st.markdown(DISCLAIMER)
    st.divider()

    with st.form("research_form"):
        col1, col2 = st.columns(2)
        with col1:
            ticker = st.text_input("Ticker (NSE Symbol)", value="RELIANCE").upper()
            current_price = st.number_input("Current Price (₹)", value=2850.0, min_value=0.01)
            market_cap_cr = st.number_input("Market Cap (₹ Cr)", value=1930000.0, min_value=1.0)
            eps = st.number_input("EPS (₹)", value=96.0)
            book_value = st.number_input("Book Value/Share (₹)", value=850.0)
        with col2:
            debt_cr = st.number_input("Total Debt (₹ Cr)", value=312000.0)
            cash_cr = st.number_input("Cash & Equivalents (₹ Cr)", value=180000.0)
            ebitda_cr = st.number_input("EBITDA (₹ Cr)", value=160000.0)
            fcf_cr = st.number_input("Free Cash Flow (₹ Cr)", value=45000.0)
            dividend_per_share = st.number_input("Dividend/Share (₹)", value=10.0)

        business_description = st.text_area(
            "Business Description",
            value=(
                "Reliance Industries is India's largest conglomerate with diversified operations "
                "in petrochemicals, refining, oil & gas, retail, and digital services (Jio)."
            ),
            height=100,
        )

        submitted = st.form_submit_button("🚀 Run Full Research", use_container_width=True)

    if submitted:
        with st.spinner(f"Running all agents for {ticker}..."):
            try:
                orch = get_orchestrator()
                report = orch.research(
                    ticker=ticker,
                    current_price=current_price,
                    market_cap_cr=market_cap_cr,
                    statements=[],
                    business_description=business_description,
                    eps=eps or None,
                    book_value_per_share=book_value or None,
                    debt_cr=debt_cr,
                    cash_cr=cash_cr,
                    ebitda_cr=ebitda_cr,
                    fcf_cr=fcf_cr,
                    dividend_per_share=dividend_per_share,
                )
                _render_report(report)
            except Exception as exc:
                st.error(f"Research failed: {exc}")


def _render_report(report: Dict[str, Any]):
    ticker = report.get("ticker", "")
    rating = report.get("final_rating", "")

    st.divider()
    st.subheader(f"{rating_badge(rating)} {ticker} — {rating}")
    st.caption(f"Confidence: {report.get('confidence_pct', 0):.0f}% | Category: {report.get('category', '—')}")

    # Score cards
    cols = st.columns(7)
    scores = [
        ("Financial", report.get("financial_strength_score")),
        ("Valuation", report.get("valuation_score")),
        ("Moat", report.get("moat_score")),
        ("Fisher", report.get("fisher_score")),
        ("Unicorn", report.get("unicorn_score")),
        ("Sentiment", report.get("sentiment_score")),
        ("Risk ↓", report.get("risk_score")),
    ]
    for col, (label, score) in zip(cols, scores):
        col.metric(label, fmt(score, 1) + "/10" if score is not None else "—")

    st.divider()

    # Key ratios
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("P/E", fmt(report.get("pe_ratio")))
    col2.metric("P/B", fmt(report.get("pb_ratio")))
    col3.metric("EV/EBITDA", fmt(report.get("ev_ebitda")))
    col4.metric("PEG", fmt(report.get("peg_ratio")))

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("ROE", pct(report.get("roe")))
    col2.metric("D/E", fmt(report.get("debt_equity")))
    col3.metric("Rev CAGR 3Y", pct(report.get("revenue_cagr_3y")))
    col4.metric("Div Yield", pct(report.get("dividend_yield")))

    st.divider()

    # Analysis columns
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("📖 Business Summary")
        st.write(report.get("business_summary", "—"))

        st.subheader("🏰 Moat Analysis")
        st.write(report.get("moat_summary", "—"))

        st.subheader("🔭 Philip Fisher Analysis")
        st.write(report.get("fisher_summary", "—"))
        if report.get("ten_x_potential"):
            st.success("✨ 10x return potential identified by Fisher analysis")
        if report.get("growth_ceiling"):
            st.caption(f"Growth ceiling: {report['growth_ceiling'].upper()}")
        for sig in report.get("scuttlebutt_signals", []):
            st.caption(f"• {sig}")

    with col2:
        st.subheader("🦄 Unicorn Potential")
        st.write(report.get("unicorn_summary", "—"))
        if report.get("ten_x_candidate"):
            st.success("🚀 10x Unicorn Candidate")
        if report.get("emerging_themes"):
            st.caption("Emerging themes: " + ", ".join(report["emerging_themes"]))
        for trigger in report.get("watch_triggers", []):
            st.caption(f"• Watch: {trigger}")

        st.subheader("📰 News & Sentiment")
        sentiment_icon = {"Positive": "🟢", "Bullish": "🟢", "Negative": "🔴", "Bearish": "🔴"}.get(
            report.get("news_sentiment"), "🟡"
        )
        st.write(f"{sentiment_icon} **News:** {report.get('news_summary', '—')}")
        st.write(f"Market Sentiment: {report.get('market_sentiment', '—')}")
        if report.get("hype_detected"):
            st.warning("⚠️ Hype detected — exercise caution")
        if report.get("accumulation_signal"):
            st.info("📈 Accumulation signal detected")
        st.caption(f"Retail buzz: {report.get('retail_buzz_level', '—')}")

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("🐂 Bull Case")
        for point in report.get("bull_case", []):
            st.write(f"• {point}")
    with col2:
        st.subheader("🐻 Bear Case")
        for point in report.get("bear_case", []):
            st.write(f"• {point}")

    if report.get("red_flags"):
        st.subheader("🚩 Red Flags")
        for flag in report["red_flags"]:
            st.error(f"🚩 {flag.get('key', '')} — {flag.get('description', '')}")

    if report.get("dcf_intrinsic_value"):
        st.info(f"💰 DCF Intrinsic Value (with 30% MoS): ₹{report['dcf_intrinsic_value']:.2f}")

    with st.expander("📊 Raw JSON Report"):
        st.json(report)


def page_morning_report():
    st.header("🌅 Morning Report — Top Picks")
    st.markdown(DISCLAIMER)
    st.divider()

    st.info(
        "Enter your watchlist below. The system will run full research on all stocks "
        "and rank them across 6 categories."
    )

    watchlist_json = st.text_area(
        "Watchlist (JSON array)",
        height=250,
        value=json.dumps([
            {
                "ticker": "RELIANCE",
                "current_price": 2850.50,
                "market_cap_cr": 1930000,
                "business_description": "Reliance Industries is India's largest conglomerate with operations in petrochemicals, refining, retail, and digital services (Jio).",
                "eps": 96.0,
                "book_value_per_share": 850.0,
                "debt_cr": 312000,
                "cash_cr": 180000,
                "ebitda_cr": 160000,
                "fcf_cr": 45000,
                "dividend_per_share": 10.0,
            },
            {
                "ticker": "DIXON",
                "current_price": 14500,
                "market_cap_cr": 8700,
                "business_description": "Dixon Technologies is India's largest electronics manufacturing services company making TVs, mobiles, and home appliances for global brands. Key beneficiary of PLI scheme and China+1 strategy.",
                "eps": 120.0,
                "book_value_per_share": 400.0,
                "debt_cr": 500,
                "cash_cr": 800,
                "ebitda_cr": 600,
                "fcf_cr": 200,
                "shares_outstanding_cr": 0.60,
                "dividend_per_share": 5.0,
            },
            {
                "ticker": "HAL",
                "current_price": 4200,
                "market_cap_cr": 141000,
                "business_description": "Hindustan Aeronautics Limited is India's state-owned aerospace and defense manufacturer producing fighter jets, helicopters, and avionics. Key beneficiary of defense indigenisation.",
                "eps": 100.0,
                "book_value_per_share": 600.0,
                "debt_cr": 0,
                "cash_cr": 12000,
                "ebitda_cr": 7000,
                "fcf_cr": 4000,
                "dividend_per_share": 35.0,
            },
        ], indent=2),
    )

    if st.button("🚀 Run Morning Report", use_container_width=True):
        try:
            watchlist = json.loads(watchlist_json)
        except json.JSONDecodeError as exc:
            st.error(f"Invalid JSON: {exc}")
            return

        with st.spinner(f"Analysing {len(watchlist)} stocks across all agents..."):
            try:
                orch = get_daily_orchestrator()
                report = orch.run(watchlist)
                _render_morning_report(report)
            except Exception as exc:
                st.error(f"Report generation failed: {exc}")


def _render_morning_report(report: Dict[str, Any]):
    st.divider()
    st.subheader(f"📊 Morning Report — {report.get('generated_at', '')[:10]}")
    st.caption(f"Stocks analysed: {report.get('stocks_analysed', 0)}")

    categories = [
        ("🏦 Top Buffett Stocks", "top_buffett_stocks"),
        ("📈 Top Growth Stocks", "top_growth_stocks"),
        ("🦄 Top Small Cap Opportunities", "top_small_cap_opportunities"),
        ("🌱 Top Emerging Theme Stocks", "top_emerging_theme_stocks"),
        ("💰 Top Dividend Stocks", "top_dividend_stocks"),
        ("🔭 Top Philip Fisher Stocks", "top_fisher_stocks"),
    ]

    for title, key in categories:
        picks = report.get(key, [])
        st.subheader(title)
        if not picks:
            st.caption("No qualifying stocks found.")
            continue
        cols = st.columns(len(picks)) if picks else []
        for col, pick in zip(cols, picks):
            with col:
                st.metric(pick["ticker"], rating_badge(pick["final_rating"]))
                st.caption(f"Score: {pick['score']:.2f}")
                m = pick.get("key_metrics", {})
                st.caption(f"ROE: {pct(m.get('roe_pct', 0) / 100 if m.get('roe_pct') else None)}")
                st.caption(f"Risk: {fmt(m.get('risk_score'), 1)}/10")
                if m.get("ten_x_potential") or m.get("ten_x_candidate"):
                    st.caption("✨ 10x potential")
                if m.get("emerging_themes"):
                    st.caption("🌱 " + ", ".join(m["emerging_themes"][:2]))

    st.divider()
    st.subheader("🚫 Stocks to Avoid")
    avoid = report.get("stocks_to_avoid", [])
    if avoid:
        for pick in avoid:
            with st.expander(f"🔴 {pick['ticker']} — Risk Score: {pick.get('key_metrics', {}).get('risk_score', '?')}"):
                st.write(f"Red flags: {', '.join(pick.get('red_flags', [])) or 'None'}")
                for point in pick.get("bear_case", []):
                    st.write(f"• {point}")
    else:
        st.caption("No stocks flagged for avoidance.")

    st.info(report.get("portfolio_rebalancing_note", ""))

    with st.expander("📊 Full Report JSON"):
        st.json(report)


def page_universe_scanner():
    st.header("🌏 NSE/BSE Universe Scanner")
    st.markdown(DISCLAIMER)
    st.divider()

    st.info(
        "Scans the NSE universe in two stages:\n"
        "1. **Stage 1** — Fast rule-based filter (ROE, D/E, revenue, FCF) across all stocks\n"
        "2. **Stage 2** — Full 9-agent research pipeline on top candidates\n\n"
        "Output: **Top 10 per category** — Buffett · Lynch · Fisher · Growth · Small Cap · "
        "Emerging Themes · Dividend · Avoid"
    )

    col1, col2 = st.columns(2)
    with col1:
        stage1_n = st.slider("Stage 1 candidates (pre-filter output)", 20, 200, 100, step=10)
        stage2_n = st.slider("Stage 2 deep analysis count", 10, 100, 30, step=5,
                              help="Lower = faster. Each stock runs 4 LLM calls.")
    with col2:
        custom_symbols = st.text_area(
            "Custom symbol list (optional, one per line)",
            placeholder="Leave blank to use NSE NIFTY 500\nOr enter:\nRELIANCE\nTCS\nINFY",
            height=120,
        )
        st.caption(f"Default covers {len(NIFTY100_FALLBACK)} symbols (NIFTY 100 + mid/small caps)")

    est_mins = max(2, stage2_n * 0.3)
    st.caption(f"Estimated duration: ~{est_mins:.0f}–{est_mins*2:.0f} minutes")

    if st.button("🚀 Start Universe Scan", use_container_width=True, type="primary"):
        symbol_list = None
        if custom_symbols.strip():
            symbol_list = [s.strip().upper() for s in custom_symbols.strip().splitlines() if s.strip()]
            st.caption(f"Using {len(symbol_list)} custom symbols")

        progress_bar = st.progress(0)
        status_text = st.empty()

        def progress_cb(stage, done, total, message=""):
            pct = int(done / total * 100) if total > 0 else 0
            progress_bar.progress(pct)
            status_text.caption(f"[{stage.upper()}] {message} ({done}/{total})")

        with st.spinner("Running universe scan..."):
            try:
                scanner = UniverseScanOrchestrator(config=get_config())
                result = scanner.run(
                    symbol_list=symbol_list,
                    stage1_top_n=stage1_n,
                    stage2_top_n=stage2_n,
                    progress_callback=progress_cb,
                )
                progress_bar.progress(100)
                status_text.success("Scan complete!")
                _render_universe_report(result)
            except Exception as exc:
                st.error(f"Scan failed: {exc}")


def _render_universe_report(result: Dict[str, Any]):
    stats = result.get("scan_stats", {})
    st.divider()

    # Stats row
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Symbols Scanned", stats.get("symbols_scanned", 0))
    col2.metric("Passed Filter", stats.get("passed_prefilter", 0))
    col3.metric("Deep Analysed", stats.get("deep_analysed", 0))
    col4.metric("Strong Candidates", stats.get("strong_candidates", 0))
    col5.metric("Duration", f"{result.get('duration_seconds', 0):.0f}s")

    st.divider()

    categories = [
        ("🏦 Top 10 Buffett Stocks", "top10_buffett", "High ROE · Strong Moat · Low Debt · Positive FCF"),
        ("📈 Top 10 Peter Lynch Stocks", "top10_lynch", "PEG < 1 · Consistent Earnings Growth · Sector Leadership"),
        ("🔭 Top 10 Philip Fisher Stocks", "top10_fisher", "Innovation · Management Vision · Future Monopoly · 10x Potential"),
        ("🚀 Top 10 Growth Stocks", "top10_growth", "High Revenue & Profit CAGR · Expanding Markets"),
        ("🦄 Top 10 Small Cap Opportunities", "top10_small_cap", "Market Cap < ₹5,000 Cr · Founder-led · High Growth"),
        ("🌱 Top 10 Emerging Theme Stocks", "top10_emerging_themes", "Defense · AI · EV · Renewables · Fintech"),
        ("💰 Top 10 Dividend Stocks", "top10_dividend", "High Yield · Consistent Payer · Low Risk"),
    ]

    for title, key, subtitle in categories:
        picks = result.get(key, [])
        st.subheader(title)
        st.caption(subtitle)
        if not picks:
            st.caption("No qualifying stocks found in this category.")
            st.divider()
            continue

        # Table view
        table_data = []
        for i, p in enumerate(picks, 1):
            m = p.get("key_metrics", {})
            table_data.append({
                "#": i,
                "Ticker": p["ticker"],
                "Name": (p.get("name") or "")[:25],
                "Sector": (p.get("sector") or "")[:20],
                "Rating": p.get("final_rating", "—"),
                "Score": p.get("score", 0),
                "P/E": fmt(m.get("pe_ratio")),
                "ROE%": f"{m.get('roe_pct', 0):.1f}",
                "Rev CAGR%": f"{m.get('revenue_cagr_3y_pct', 0):.1f}",
                "Risk": fmt(m.get("risk_score"), 1),
                "10x?": "✨" if (m.get("ten_x_potential") or m.get("ten_x_candidate")) else "",
            })
        st.dataframe(table_data, use_container_width=True)

        # Expandable details for each pick
        for p in picks[:3]:  # show detail expanders for top 3
            with st.expander(f"📋 {p['ticker']} — {p.get('name', '')}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.write("**Synopsis:**", p.get("synopsis", "—"))
                    st.write("**Bull Case:**")
                    for b in p.get("bull_case", []):
                        st.write(f"• {b}")
                with c2:
                    st.write("**Bear Case:**")
                    for b in p.get("bear_case", []):
                        st.write(f"• {b}")
                    if p.get("red_flags"):
                        st.error("Red flags: " + ", ".join(p["red_flags"]))
                    if p.get("watch_triggers"):
                        st.info("Watch for: " + " · ".join(p["watch_triggers"]))
        st.divider()

    # Avoid list
    st.subheader("🚫 Top 10 Stocks to Avoid")
    avoid = result.get("top10_avoid", [])
    if avoid:
        for p in avoid:
            flags = ", ".join(p.get("red_flags") or []) or "Multiple risk factors"
            with st.expander(f"🔴 {p['ticker']} — Risk Score: {p.get('key_metrics', {}).get('risk_score', '?')} | {flags}"):
                for b in p.get("bear_case", []):
                    st.write(f"• {b}")
    else:
        st.caption("No high-risk stocks flagged.")

    st.divider()
    st.info(result.get("portfolio_rebalancing_note", ""))
    st.caption(f"Data sources: {', '.join(result.get('data_sources', []))}")
    st.caption(result.get("data_source_note", ""))

    with st.expander("📊 Full Scan JSON"):
        st.json({k: v for k, v in result.items() if k != "all_reports_summary"})


def page_about():
    st.header("ℹ️ About the Investment Research Wizard")
    st.markdown("""
    ## Multi-Agent Architecture

    This system uses **9 specialized AI agents** to analyse Indian equities:

    | Agent | Philosophy | What it measures |
    |---|---|---|
    | 🏦 **Fundamental Agent** | Buffett/Graham | ROE, D/E, FCF, Revenue CAGR |
    | 📊 **Valuation Agent** | Graham/Lynch | P/E, P/B, PEG, DCF with MoS |
    | 🏰 **Moat Agent** | Buffett | Brand, switching cost, network effects |
    | 🔭 **Philip Fisher Agent** | P. Fisher | R&D, management vision, 10x potential |
    | 📰 **News Agent** | Quantitative | Facts vs hype, regulatory signals |
    | 📡 **Sentiment Agent** | Contrarian | RSS feeds, buzz level, accumulation |
    | 🦄 **Unicorn Detector** | VC-style | Small cap, founder-led, emerging sector |
    | ⚠️ **Risk Agent** | Howard Marks | Red flags, governance, debt traps |
    | 🎯 **Orchestrator** | Synthesis | Final rating, category, confidence |

    ## Output Categories
    - **Long-term Compounder** — Buffett + Fisher quality stocks
    - **Undervalued Value** — Graham-style value plays
    - **Turnaround** — Recovering from temporary difficulty
    - **Dividend / Income** — Steady yield payers
    - **Momentum (Risky)** — High growth, elevated risk
    - **Avoid / Watchlist** — Red flags present

    ## Morning Report
    Every morning, the system produces **Top 3 picks** across:
    Buffett · Growth · Small Cap · Emerging Themes · Dividend · Fisher · Avoid

    ---
    """)
    st.markdown(DISCLAIMER)


# ------------------------------------------------------------------
# Sidebar navigation
# ------------------------------------------------------------------

st.sidebar.image("https://img.icons8.com/emoji/96/chart-increasing-emoji.png", width=64)
st.sidebar.title("Investment Research Wizard")
st.sidebar.caption("NSE/BSE · AI-Powered · Paper Trading")

page = st.sidebar.radio(
    "Navigate",
    ["Single Stock Research", "Morning Report", "Universe Scanner", "About"],
    index=0,
)

st.sidebar.divider()
st.sidebar.caption("🇮🇳 NSE/BSE Equities Only")
st.sidebar.caption("📄 Educational use only")

if page == "Single Stock Research":
    page_single_stock()
elif page == "Morning Report":
    page_morning_report()
elif page == "Universe Scanner":
    page_universe_scanner()
else:
    page_about()
