"""Indian Investment Research Wizard — Streamlit Dashboard."""
import json
import time
from typing import Any, Dict, List

import streamlit as st

from src.agents.orchestrator import Orchestrator
from src.agents.daily_report import DailyReportOrchestrator
from src.agents.universe_scan import UniverseScanOrchestrator
from src.agents.universe_screener import NIFTY100_FALLBACK
from src.agents.unicorn_hunter import UnicornHunterAgent, UNICORN_UNIVERSE
from src.agents.ipo_agent import IPODataAgent
from src.agents.ipo_unicorn_hunter import IPOUnicornHunterAgent
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


def page_unicorn_hunt():
    st.header("🦄 Unicorn Hunter — Next NIFTY 50 Candidates")
    st.markdown(DISCLAIMER)
    st.info(
        "Scans **300+ undiscovered small/mid-cap stocks** (max ₹15,000 Cr market cap). "
        "Deliberately **excludes** large-cap household names like TCS, Infosys, HDFC, Reliance. "
        "Goal: find the next multi-bagger **before** the market discovers it."
    )
    st.divider()

    col1, col2 = st.columns([2, 1])
    with col1:
        top_n = st.slider("Top N Unicorn Candidates", min_value=5, max_value=50, value=20, step=5)
    with col2:
        use_custom = st.checkbox("Use custom symbol list", value=False)

    custom_symbols = None
    if use_custom:
        raw = st.text_area(
            "Custom NSE symbols (one per line)",
            value="\n".join(["IDEAFORGE", "MTAR", "KAYNES", "WAAREEENER", "LAURUS"]),
            height=100,
        )
        custom_symbols = [s.strip().upper() for s in raw.splitlines() if s.strip()]

    universe_size = len(custom_symbols or UNICORN_UNIVERSE)
    st.caption(f"Will scan **{universe_size} symbols** across emerging sectors.")

    if st.button("🚀 Start Unicorn Hunt", type="primary"):
        hunter = UnicornHunterAgent(config=get_config())

        progress_bar = st.progress(0, text="Initialising hunt...")
        status_text = st.empty()

        def on_progress(done, total):
            pct_done = done / total if total else 0
            progress_bar.progress(pct_done, text=f"Scanning {done}/{total} stocks...")

        with st.spinner("Hunting for undiscovered gems..."):
            result = hunter.hunt(
                symbol_list=custom_symbols,
                top_n=top_n,
                progress_callback=on_progress,
            )

        progress_bar.progress(1.0, text="Hunt complete!")

        st.success(result.get("hunt_note", "Hunt complete."))

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Scanned", result["total_scanned"])
        col2.metric("Passed Filters", result["passed_filter"])
        col3.metric("Returned", result["candidates_returned"])
        col4.metric("Fetch Failures", result["fetch_failures"])

        st.divider()

        # Theme breakdown
        if result.get("theme_breakdown"):
            st.subheader("🗂️ Candidates by Emerging Theme")
            theme_data = [
                {"Theme": theme, "Tickers": ", ".join(tickers[:8]) + ("..." if len(tickers) > 8 else ""), "Count": len(tickers)}
                for theme, tickers in result["theme_breakdown"].items()
            ]
            import pandas as pd
            st.dataframe(pd.DataFrame(theme_data), use_container_width=True, hide_index=True)
            st.divider()

        # Candidate rankings
        if result["candidates"]:
            st.subheader(f"🏆 Top {len(result['candidates'])} Unicorn Candidates")

            import pandas as pd
            rows = []
            for i, c in enumerate(result["candidates"], 1):
                rows.append({
                    "#": i,
                    "Ticker": c["ticker"],
                    "Name": c.get("name", c["ticker"])[:25],
                    "Mcap (Cr)": f"₹{c.get('market_cap_cr', 0):,.0f}",
                    "Rev Growth": pct(c.get("revenue_growth_yoy")),
                    "ROE": pct(c.get("roe")),
                    "D/E": fmt(c.get("debt_equity")),
                    "Themes": ", ".join(c.get("emerging_themes", []))[:40] or "—",
                    "Composite": f"{c.get('unicorn_composite', 0):.2f}",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            st.divider()
            st.subheader("🔍 Stock Details")
            for c in result["candidates"][:10]:
                with st.expander(f"#{result['candidates'].index(c)+1} {c['ticker']} — {c.get('name', '')} | Score: {c.get('unicorn_composite', 0):.2f}"):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Market Cap", f"₹{c.get('market_cap_cr', 0):,.0f} Cr")
                    c1.metric("Price", f"₹{c.get('current_price', 0):,.2f}")
                    c2.metric("Revenue Growth", pct(c.get("revenue_growth_yoy")))
                    c2.metric("Earnings Growth", pct(c.get("earnings_growth_yoy")))
                    c3.metric("ROE", pct(c.get("roe")))
                    c3.metric("Debt/Equity", fmt(c.get("debt_equity")))

                    st.write(f"**Sector:** {c.get('sector', '—')} | **Industry:** {c.get('industry', '—')}")
                    st.write(f"**Emerging Themes:** {', '.join(c.get('emerging_themes', [])) or 'None detected'}")

                    scores_c1, scores_c2 = st.columns(2)
                    scores_c1.write(f"Growth Score: {score_bar(c.get('unicorn_growth_score'))}")
                    scores_c1.write(f"Size Score: {score_bar(c.get('unicorn_size_score'))}")
                    scores_c1.write(f"Theme Score: {score_bar(c.get('unicorn_theme_score'))}")
                    scores_c2.write(f"Quality Score: {score_bar(c.get('unicorn_quality_score'))}")
                    scores_c2.write(f"Valuation Score: {score_bar(c.get('unicorn_valuation_score'))}")
                    scores_c2.write(f"**Composite: {score_bar(c.get('unicorn_composite'))}**")

                    if c.get("business_description"):
                        st.caption(c["business_description"][:300])
        else:
            st.warning(
                "No unicorn candidates found. This usually means yfinance couldn't fetch data "
                "for the symbols, or all were filtered out. Try with a smaller custom list first."
            )

        st.divider()
        st.caption(DISCLAIMER.replace("⚠️ **Disclaimer:** ", ""))


def _ipo_table(records: List[Dict[str, Any]], empty_message: str):
    if not records:
        st.info(empty_message)
        return
    import pandas as pd
    rows = [{
        "Symbol": r.get("symbol") or "—",
        "Company": (r.get("company_name") or "—")[:35],
        "Series": r.get("series", "—"),
        "Price Band": (
            f"₹{r['issue_price_min']:.0f}–₹{r['issue_price_max']:.0f}"
            if r.get("issue_price_min") and r.get("issue_price_max") else "—"
        ),
        "Open": r.get("open_date") or "—",
        "Close": r.get("close_date") or "—",
        "Listing Date": r.get("listing_date") or "—",
        "Days Since Listing": r.get("days_since_listing", "—"),
    } for r in records]
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def page_ipo_watch():
    st.header("📋 IPO Watch — SEBI / NSE / BSE IPO Details")
    st.markdown(DISCLAIMER)
    st.info(
        "IPO issue price, size, and dates are SEBI-mandated disclosures, surfaced here "
        "via NSE's public IPO endpoints (BSE has no comparably stable public JSON "
        "endpoint — cross-check bseindia.com/publicissue for BSE-only issues)."
    )
    st.divider()

    if st.button("🔄 Refresh IPO Lists", type="primary"):
        agent = IPODataAgent(config=get_config())
        try:
            with st.spinner("Fetching current, upcoming, and recently-listed IPOs..."):
                st.session_state["ipo_current"] = agent.fetch_current_ipos()
                st.session_state["ipo_upcoming"] = agent.fetch_upcoming_ipos()
                st.session_state["ipo_recent"] = agent.fetch_recently_listed_ipos()
        finally:
            agent.close()

    st.subheader("🟢 Currently Open")
    _ipo_table(
        st.session_state.get("ipo_current", []),
        "No open IPOs loaded yet — click **Refresh IPO Lists** above.",
    )

    st.subheader("🔵 Upcoming")
    _ipo_table(
        st.session_state.get("ipo_upcoming", []),
        "No upcoming IPOs loaded yet — click **Refresh IPO Lists** above.",
    )

    st.subheader("⚪ Recently Listed")
    _ipo_table(
        st.session_state.get("ipo_recent", []),
        "No recently-listed IPOs loaded yet — click **Refresh IPO Lists** above.",
    )

    st.divider()
    st.header("🦄 IPO Unicorn Hunt — Next NIFTY 50 Among Fresh Listings")
    st.info(
        "Loads all IPOs listed within the lookback window and scores them for "
        "next-unicorn potential using the same growth/quality/theme framework as the "
        "regular Unicorn Hunt, plus a bonus for how recently they listed."
    )

    col1, col2 = st.columns(2)
    with col1:
        lookback_months = st.slider("Lookback window (months)", min_value=1, max_value=36, value=12)
    with col2:
        top_n = st.slider("Top N IPO Unicorn Candidates", min_value=5, max_value=50, value=20, step=5)

    if st.button("🚀 Start IPO Unicorn Hunt", type="primary"):
        hunter = IPOUnicornHunterAgent(config=get_config())

        progress_bar = st.progress(0, text="Loading recently-listed IPOs...")

        def on_progress(done, total):
            pct_done = done / total if total else 0
            progress_bar.progress(pct_done, text=f"Scanning {done}/{total} IPOs...")

        with st.spinner("Hunting for the next unicorn among fresh listings..."):
            result = hunter.hunt(months=lookback_months, top_n=top_n, progress_callback=on_progress)

        progress_bar.progress(1.0, text="Hunt complete!")
        st.success(result.get("hunt_note", "Hunt complete."))

        col1, col2, col3 = st.columns(3)
        col1.metric("IPOs Scanned", result.get("total_scanned", 0))
        col2.metric("Passed Filters", result.get("passed_filter", 0))
        col3.metric("Returned", result.get("candidates_returned", 0))

        st.divider()

        if result["candidates"]:
            st.subheader(f"🏆 Top {len(result['candidates'])} IPO Unicorn Candidates")

            import pandas as pd
            rows = []
            for i, c in enumerate(result["candidates"], 1):
                rows.append({
                    "#": i,
                    "Ticker": c["ticker"],
                    "Name": c.get("name", c["ticker"])[:25],
                    "Listed": c.get("ipo_listing_date") or "—",
                    "Days Since Listing": c.get("days_since_listing", "—"),
                    "Listing Gain": pct((c.get("listing_gain_pct") or 0) / 100) if c.get("listing_gain_pct") is not None else "—",
                    "Rev Growth": pct(c.get("revenue_growth_yoy")),
                    "Recency Bonus": f"+{c.get('ipo_recency_bonus', 0):.1f}",
                    "Composite": f"{c.get('unicorn_composite', 0):.2f}",
                })
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

            st.divider()
            st.subheader("🔍 Candidate Details")
            for i, c in enumerate(result["candidates"][:10], 1):
                with st.expander(f"#{i} {c['ticker']} — {c.get('name', '')} | Score: {c.get('unicorn_composite', 0):.2f}"):
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Market Cap", f"₹{c.get('market_cap_cr', 0):,.0f} Cr")
                    c1.metric("Current Price", f"₹{c.get('current_price', 0):,.2f}")
                    c2.metric("Issue Price (max)", f"₹{c.get('ipo_issue_price_max', 0) or 0:,.2f}")
                    c2.metric("Listing Gain", pct((c.get("listing_gain_pct") or 0) / 100) if c.get("listing_gain_pct") is not None else "—")
                    c3.metric("Days Since Listing", c.get("days_since_listing", "—"))
                    c3.metric("Recency Bonus", f"+{c.get('ipo_recency_bonus', 0):.1f}")

                    st.write(f"**Sector:** {c.get('sector', '—')} | **Industry:** {c.get('industry', '—')}")
                    st.write(f"**Emerging Themes:** {', '.join(c.get('emerging_themes', [])) or 'None detected'}")
                    st.write(f"Composite Score: {score_bar(c.get('unicorn_composite'))}")

                    if c.get("business_description"):
                        st.caption(c["business_description"][:300])
        else:
            st.warning(
                "No IPO unicorn candidates found. This usually means NSE's IPO endpoint "
                "was unreachable, no IPOs listed within the lookback window, or all were "
                "filtered out. Try widening the lookback window."
            )

        st.divider()
        st.caption(DISCLAIMER.replace("⚠️ **Disclaimer:** ", ""))


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
    ["Single Stock Research", "Morning Report", "Universe Scanner", "Unicorn Hunt", "IPO Watch", "About"],
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
elif page == "Unicorn Hunt":
    page_unicorn_hunt()
elif page == "IPO Watch":
    page_ipo_watch()
else:
    page_about()
