"""Master orchestrator — coordinates all agents to produce a research report for a stock."""
from typing import Any, Dict, List, Optional

import anthropic

from src.agents.data_collector import DataCollectorAgent
from src.agents.fundamental_agent import FundamentalAgent
from src.agents.valuation_agent import ValuationAgent
from src.agents.moat_agent import MoatAgent
from src.agents.risk_agent import RiskAgent
from src.agents.news_agent import NewsAgent
from src.data.models import FinalRating, StockCategory
from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.validators import validate_ticker

logger = get_logger(__name__)

DISCLAIMER = (
    "This is educational research, not financial advice. "
    "Consult a SEBI-registered investment adviser before investing."
)

SYNTHESIS_SYSTEM_PROMPT = """You are the Indian Investment Research Wizard.
Given structured analysis data for a stock, produce a final research synthesis.
Respond as JSON with these keys:
- business_summary: 3-5 sentences on what the company does and how it makes money
- bull_case: 2-3 bullet points (strongest positives)
- bear_case: 2-3 bullet points (key risks and negatives)
- ideal_investor_type: who should consider this stock (e.g., "Long-term value investor with 5+ year horizon")
- final_rating: one of "Strong Research Candidate" | "Watch" | "Avoid"
- confidence_pct: 0-100 reflecting certainty of the rating
- category: one of "long_term_compounder" | "undervalued_value" | "turnaround" | "dividend_income" | "momentum_risky" | "avoid_watchlist"

Rules:
- A stock is "Strong Research Candidate" ONLY if business quality, financials, valuation, and governance are ALL acceptable.
- Never use the word "guaranteed" or promise returns.
- Always note the most important risk.
Disclaimer: This is educational research, not financial advice."""


class Orchestrator:
    """
    Runs all agents in sequence for a given ticker and synthesises a research report.
    """

    def __init__(self, config=None):
        self.cfg = config or get_config()
        self.data_agent = DataCollectorAgent(config=self.cfg)
        self.fundamental_agent = FundamentalAgent()
        self.valuation_agent = ValuationAgent()
        self.moat_agent = MoatAgent(config=self.cfg)
        self.risk_agent = RiskAgent()
        self.news_agent = NewsAgent(config=self.cfg)
        self._llm: Optional[anthropic.Anthropic] = None
        if self.cfg.llm.anthropic_api_key:
            self._llm = anthropic.Anthropic(api_key=self.cfg.llm.anthropic_api_key)

    def research(
        self,
        ticker: str,
        current_price: float,
        market_cap_cr: float,
        statements: List[Dict[str, Any]],
        business_description: str,
        eps: Optional[float] = None,
        book_value_per_share: Optional[float] = None,
        debt_cr: float = 0.0,
        cash_cr: float = 0.0,
        ebitda_cr: float = 0.0,
        fcf_cr: float = 0.0,
        shares_outstanding_cr: float = 1.0,
        dividend_per_share: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Full research pipeline for a single stock.
        Returns a structured research report.
        """
        validated = validate_ticker(ticker)
        logger.info("=== Research pipeline started for %s ===", validated)

        # 1. Fundamental analysis
        fundamental = self.fundamental_agent.analyze(validated, statements)
        profit_cagr = fundamental.get("profit_cagr_3y")

        # 2. Valuation
        valuation = self.valuation_agent.analyze(
            validated, current_price, market_cap_cr,
            eps, book_value_per_share, debt_cr, cash_cr,
            ebitda_cr, fcf_cr, shares_outstanding_cr,
            profit_cagr, dividend_per_share,
        )

        # 3. Moat
        moat = self.moat_agent.analyze(validated, business_description)

        # 4. News
        articles = self.data_agent.fetch_news(validated)
        news = self.news_agent.analyze(validated, articles)

        # 5. Risk (combines all signals)
        risk_data = {
            **fundamental,
            **valuation,
            "operating_cash_flow_cr": fcf_cr,
        }
        risk = self.risk_agent.analyze(validated, risk_data)

        # 6. LLM synthesis
        synthesis = self._synthesize(validated, fundamental, valuation, moat, risk, news)

        report = {
            "ticker": validated,
            "current_price": current_price,
            "market_cap_cr": market_cap_cr,
            # Scores
            "financial_strength_score": fundamental.get("financial_strength_score"),
            "growth_score": self._growth_score(fundamental),
            "valuation_score": valuation.get("valuation_score"),
            "moat_score": moat.get("moat_score"),
            "risk_score": risk.get("risk_score"),
            # Ratios
            "pe_ratio": valuation.get("pe_ratio"),
            "pb_ratio": valuation.get("pb_ratio"),
            "ev_ebitda": valuation.get("ev_ebitda"),
            "peg_ratio": valuation.get("peg_ratio"),
            "dividend_yield": valuation.get("dividend_yield"),
            "dcf_intrinsic_value": valuation.get("intrinsic_value_with_mos"),
            # Fundamental metrics
            "roe": fundamental.get("roe"),
            "debt_equity": fundamental.get("debt_equity"),
            "revenue_cagr_3y": fundamental.get("revenue_cagr_3y"),
            "profit_cagr_3y": profit_cagr,
            "fcf_cr": fundamental.get("fcf_cr"),
            "promoter_holding_pct": fundamental.get("promoter_holding_pct"),
            "promoter_pledge_pct": fundamental.get("promoter_pledge_pct"),
            # Qualitative
            "red_flags": risk.get("red_flags", []),
            "news_sentiment": news.get("sentiment"),
            "news_summary": news.get("summary"),
            "moat_summary": moat.get("moat_summary"),
            # Synthesis
            **synthesis,
            "disclaimer": DISCLAIMER,
        }
        logger.info(
            "Research complete for %s | rating=%s | confidence=%.0f%%",
            validated, report.get("final_rating"), report.get("confidence_pct", 0),
        )
        return report

    def _growth_score(self, fundamental: Dict[str, Any]) -> float:
        rev_cagr = fundamental.get("revenue_cagr_3y") or 0
        profit_cagr = fundamental.get("profit_cagr_3y") or 0
        avg = (rev_cagr + profit_cagr) / 2
        if avg >= 0.20:
            return 10.0
        if avg >= 0.15:
            return 8.0
        if avg >= 0.10:
            return 6.0
        if avg >= 0.05:
            return 4.0
        return 2.0

    def _synthesize(
        self,
        ticker: str,
        fundamental: Dict,
        valuation: Dict,
        moat: Dict,
        risk: Dict,
        news: Dict,
    ) -> Dict[str, Any]:
        if not self._llm:
            return self._rule_based_synthesis(fundamental, valuation, moat, risk)

        data_summary = {
            "ticker": ticker,
            "financial_strength_score": fundamental.get("financial_strength_score"),
            "roe": fundamental.get("roe"),
            "debt_equity": fundamental.get("debt_equity"),
            "revenue_cagr_3y": fundamental.get("revenue_cagr_3y"),
            "profit_cagr_3y": fundamental.get("profit_cagr_3y"),
            "pe_ratio": valuation.get("pe_ratio"),
            "pb_ratio": valuation.get("pb_ratio"),
            "peg_ratio": valuation.get("peg_ratio"),
            "valuation_score": valuation.get("valuation_score"),
            "moat_score": moat.get("moat_score"),
            "moat_summary": moat.get("moat_summary"),
            "risk_score": risk.get("risk_score"),
            "red_flags": [f["key"] for f in risk.get("red_flags", [])],
            "news_sentiment": news.get("sentiment"),
            "news_key_facts": news.get("key_facts", []),
        }

        import json
        user_msg = f"Analyze this stock data and produce a research synthesis:\n\n{json.dumps(data_summary, indent=2)}"
        try:
            msg = self._llm.messages.create(
                model=self.cfg.llm.model,
                max_tokens=2048,
                system=SYNTHESIS_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
            )
            return json.loads(msg.content[0].text.strip())
        except Exception as exc:
            logger.error("LLM synthesis failed for %s: %s", ticker, exc)
            return self._rule_based_synthesis(fundamental, valuation, moat, risk)

    def _rule_based_synthesis(
        self, fundamental: Dict, valuation: Dict, moat: Dict, risk: Dict
    ) -> Dict[str, Any]:
        fs = fundamental.get("financial_strength_score", 5)
        vs = valuation.get("valuation_score", 5)
        ms = moat.get("moat_score", 5)
        rs = risk.get("risk_score", 5)

        if fs >= 7 and vs >= 6 and ms >= 6 and rs <= 3:
            rating = "Strong Research Candidate"
            confidence = 75.0
            category = "long_term_compounder"
        elif rs >= 7:
            rating = "Avoid"
            confidence = 80.0
            category = "avoid_watchlist"
        else:
            rating = "Watch"
            confidence = 55.0
            category = "undervalued_value"

        return {
            "business_summary": "LLM not configured — rule-based synthesis applied.",
            "bull_case": ["Strong financials", "Good moat score"] if fs >= 7 else ["Some positive attributes"],
            "bear_case": [f["description"] for f in risk.get("red_flags", [])[:2]] or ["Monitor closely"],
            "ideal_investor_type": "Long-term value investor" if rating == "Strong Research Candidate" else "Cautious investor",
            "final_rating": rating,
            "confidence_pct": confidence,
            "category": category,
        }
