"""Master orchestrator — coordinates all agents to produce a research report for a stock."""
from typing import Any, Dict, List, Optional

import anthropic

from src.agents.data_collector import DataCollectorAgent
from src.agents.fundamental_agent import FundamentalAgent
from src.agents.valuation_agent import ValuationAgent
from src.agents.registry import AgentRegistry
from src.agents.risk_agent import RiskAgent
# Importing these registers them with AgentRegistry (see src/agents/registry.py).
import src.agents.moat_agent  # noqa: F401
import src.agents.news_agent  # noqa: F401
import src.agents.fisher_agent  # noqa: F401
import src.agents.sentiment_agent  # noqa: F401
import src.agents.unicorn_detector  # noqa: F401
from src.data.models import FinalRating, StockCategory
from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.prompts import load_prompt
from src.utils.scoring import tiered_score
from src.utils.validators import validate_ticker

logger = get_logger(__name__)


class Orchestrator:
    """
    Runs all agents in sequence for a given ticker and synthesises a research report.

    The mandatory chain (data -> fundamental -> valuation -> risk -> synthesis) has
    real, non-uniform data dependencies and is explicit code below. The independent
    "enrichment" agents (moat, news, sentiment, fisher, unicorn by default) are
    config-driven: config.pipeline.enabled_agents (config/default.yaml) lists which
    ones run, in what order, looked up via AgentRegistry — see src/agents/registry.py
    for how to add a new one without editing this file.
    """

    def __init__(self, config=None):
        self.cfg = config or get_config()
        self.data_agent = DataCollectorAgent(config=self.cfg)
        self.fundamental_agent = FundamentalAgent()
        self.valuation_agent = ValuationAgent()
        self.risk_agent = RiskAgent()
        self.rules = get_config().scoring.synthesis
        # Enrichment agent instances, keyed by name, built from the registry per the
        # config-declared pipeline order — NOT from self.cfg, so a mocked/partial
        # config object passed by a caller can't silently disable the pipeline.
        self.enrichment_agents = {
            name: AgentRegistry.create(name, self.cfg)
            for name in get_config().pipeline.enabled_agents
        }
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

        # 3. Enrichment agents (moat, news, sentiment, fisher, unicorn by default) —
        # config-driven; see self.enrichment_agents / config.pipeline.enabled_agents.
        articles = self.data_agent.fetch_news(validated)
        context: Dict[str, Any] = {
            "business_description": business_description,
            "market_cap_cr": market_cap_cr,
            "articles": articles,
            **fundamental,
            **valuation,
        }
        for name, agent in self.enrichment_agents.items():
            agent_cls = type(agent)
            kwargs = agent_cls.pipeline_kwargs(validated, context)
            context[name] = agent.analyze(validated, **kwargs)

        moat = context.get("moat", {})
        news = context.get("news", {})
        sentiment = context.get("sentiment", {})
        fisher = context.get("fisher", {})
        unicorn = context.get("unicorn", {})

        # 4. Risk (combines all signals)
        risk_data = {
            **fundamental,
            **valuation,
            "operating_cash_flow_cr": fcf_cr,
        }
        risk = self.risk_agent.analyze(validated, risk_data)

        # 5. LLM synthesis
        synthesis = self._synthesize(validated, fundamental, valuation, moat, risk, news, fisher, unicorn)

        report = {
            "ticker": validated,
            "current_price": current_price,
            "market_cap_cr": market_cap_cr,
            # Scores
            "financial_strength_score": fundamental.get("financial_strength_score"),
            "growth_score": self._growth_score(fundamental),
            "valuation_score": valuation.get("valuation_score"),
            "moat_score": moat.get("moat_score"),
            "fisher_score": fisher.get("fisher_score"),
            "unicorn_score": unicorn.get("unicorn_score"),
            "sentiment_score": sentiment.get("sentiment_score"),
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
            # Fisher
            "fisher_summary": fisher.get("fisher_summary"),
            "ten_x_potential": fisher.get("ten_x_potential"),
            "growth_ceiling": fisher.get("growth_ceiling"),
            "scuttlebutt_signals": fisher.get("scuttlebutt_signals", []),
            # Unicorn
            "unicorn_summary": unicorn.get("unicorn_summary"),
            "emerging_themes": unicorn.get("emerging_themes", []),
            "unicorn_size": unicorn.get("size_label"),
            "ten_x_candidate": unicorn.get("ten_x_candidate"),
            "watch_triggers": unicorn.get("watch_triggers", []),
            # Sentiment
            "market_sentiment": sentiment.get("overall_sentiment"),
            "hype_detected": sentiment.get("hype_detected"),
            "accumulation_signal": sentiment.get("accumulation_signal"),
            "retail_buzz_level": sentiment.get("retail_buzz_level"),
            # Synthesis
            **synthesis,
            "disclaimer": get_config().disclaimer,
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
        return tiered_score(avg, self.rules.growth_tiers, no_match=self.rules.growth_no_match)

    def _synthesize(
        self,
        ticker: str,
        fundamental: Dict,
        valuation: Dict,
        moat: Dict,
        risk: Dict,
        news: Dict,
        fisher: Optional[Dict] = None,
        unicorn: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        if not self._llm:
            return self._rule_based_synthesis(fundamental, valuation, moat, risk, fisher, unicorn)

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
            "fisher_score": (fisher or {}).get("fisher_score"),
            "ten_x_potential": (fisher or {}).get("ten_x_potential"),
            "unicorn_score": (unicorn or {}).get("unicorn_score"),
            "emerging_themes": (unicorn or {}).get("emerging_themes", []),
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
                max_tokens=self.cfg.llm.max_tokens_for("synthesis"),
                system=load_prompt("synthesis"),
                messages=[{"role": "user", "content": user_msg}],
            )
            return json.loads(msg.content[0].text.strip())
        except Exception as exc:
            logger.error("LLM synthesis failed for %s: %s", ticker, exc)
            return self._rule_based_synthesis(fundamental, valuation, moat, risk)

    def _rule_based_synthesis(
        self, fundamental: Dict, valuation: Dict, moat: Dict, risk: Dict,
        fisher: Optional[Dict] = None, unicorn: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        fs = fundamental.get("financial_strength_score", 5)
        vs = valuation.get("valuation_score", 5)
        ms = moat.get("moat_score", 5)
        rs = risk.get("risk_score", 5)
        fisher_score = (fisher or {}).get("fisher_score", 5)
        unicorn_score = (unicorn or {}).get("unicorn_score", 5)
        r = self.rules

        if rs >= r.avoid_risk_threshold:
            rating = "Avoid"
            confidence = r.avoid_confidence
            category = "avoid_watchlist"
        elif unicorn_score >= r.strong_unicorn_score_threshold and rs <= r.strong_unicorn_risk_max:
            rating = "Strong Research Candidate"
            confidence = r.strong_unicorn_confidence
            category = "long_term_compounder"
        elif (
            fs >= r.strong_core_financial_min and vs >= r.strong_core_valuation_min
            and ms >= r.strong_core_moat_min and rs <= r.strong_core_risk_max
        ):
            rating = "Strong Research Candidate"
            confidence = r.strong_core_confidence
            category = "long_term_compounder"
        elif fisher_score >= r.strong_fisher_score_min and unicorn_score >= r.strong_fisher_unicorn_min:
            rating = "Strong Research Candidate"
            confidence = r.strong_fisher_confidence
            category = "momentum_risky"
        else:
            rating = "Watch"
            confidence = r.watch_confidence
            category = "undervalued_value"

        bull = ["Strong financials", "Good moat score"] if fs >= 7 else []
        if (fisher or {}).get("ten_x_potential"):
            bull.append("Philip Fisher: 10x return potential identified")
        if (unicorn or {}).get("ten_x_candidate"):
            bull.append("Unicorn candidate — emerging sector tailwind")
        bull = bull or ["Some positive attributes"]

        return {
            "business_summary": "LLM not configured — rule-based synthesis applied.",
            "bull_case": bull[:3],
            "bear_case": [f["description"] for f in risk.get("red_flags", [])[:2]] or ["Monitor closely"],
            "ideal_investor_type": (
                "Growth & momentum investor" if category == "momentum_risky"
                else "Long-term value investor" if rating == "Strong Research Candidate"
                else "Cautious investor"
            ),
            "final_rating": rating,
            "confidence_pct": confidence,
            "category": category,
        }
