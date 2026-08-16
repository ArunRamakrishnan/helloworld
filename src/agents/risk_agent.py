"""Risk Agent — detects red flags and computes a risk score."""
from typing import Any, Dict, List, Optional, Tuple

from src.agents.registry import AgentRegistry
from src.utils.config import get_config
from src.utils.logger import get_logger
from src.utils.validators import validate_score

logger = get_logger(__name__)


@AgentRegistry.register("risk")
class RiskAgent:
    """
    Checks for red flags and scores risk (0 = safest, 10 = most risky).
    Lower risk score is better for investment.
    All thresholds, flag descriptions, and point values are sourced from
    config.scoring.risk (config/default.yaml).
    """

    def __init__(self, config=None):
        self.cfg = config or get_config()
        # Scoring rules always come from the real loaded config, independent of
        # whatever `config` object the caller injects (see fundamental_agent.py).
        self.rules = get_config().scoring.risk

    def detect_red_flags(self, data: Dict[str, Any]) -> List[Tuple[str, str]]:
        """
        Returns a list of (flag_key, description) tuples for each detected red flag.
        """
        flags = []
        desc = self.rules.red_flag_descriptions

        de = data.get("debt_equity")
        if de is not None and de > self.rules.high_debt_de_threshold:
            flags.append(("high_debt", desc["high_debt"]))

        fcf = data.get("fcf_cr")
        if fcf is not None and fcf < 0:
            flags.append(("negative_fcf", desc["negative_fcf"]))

        op_cf = data.get("operating_cash_flow_cr")
        if op_cf is not None and op_cf < 0:
            flags.append(("negative_cash_flow_ops", desc["negative_cash_flow_ops"]))

        pledge = data.get("promoter_pledge_pct")
        if pledge is not None and pledge > self.rules.high_promoter_pledge_pct:
            flags.append(("high_promoter_pledge", desc["high_promoter_pledge"]))

        promoter_holding = data.get("promoter_holding_pct")
        if promoter_holding is not None and promoter_holding < self.rules.low_promoter_holding_pct:
            flags.append(("low_promoter_holding", desc["low_promoter_holding"]))

        pe = data.get("pe_ratio")
        if pe is not None and pe > self.rules.overvalued_pe_threshold:
            flags.append(("overvalued_pe", desc["overvalued_pe"]))

        if data.get("auditor_changed", False):
            flags.append(("auditor_change", desc["auditor_change"]))

        if data.get("governance_issue", False):
            flags.append(("governance_issue", desc["governance_issue"]))

        if data.get("sudden_price_spike", False):
            flags.append(("sudden_price_spike", desc["sudden_price_spike"]))

        logger.info("Red flags detected for %s: %s", data.get("ticker", "?"), [f[0] for f in flags])
        return flags

    def compute_risk_score(self, red_flags: List[Tuple[str, str]], de: Optional[float]) -> float:
        """
        Risk score from 0 (no risk) to 10 (extremely risky).
        Note: for investment decisions, lower risk score is BETTER.
        Each flag adds to risk score; severe flags add more.
        """
        severe_flags = set(self.rules.severe_flags)
        score = 0.0
        for flag_key, _ in red_flags:
            score += self.rules.severe_flag_points if flag_key in severe_flags else self.rules.normal_flag_points

        # Additional debt-level penalty
        if de is not None:
            for threshold, penalty in self.rules.debt_penalty_tiers:
                if de > threshold:
                    score += penalty
                    break

        return round(min(10.0, score), 2)

    def analyze(self, ticker: str, combined_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run risk analysis and return risk score with red flag list."""
        logger.info("Risk analysis for %s", ticker)
        data = {"ticker": ticker, **combined_data}
        red_flags = self.detect_red_flags(data)
        de = combined_data.get("debt_equity")
        risk_score = self.compute_risk_score(red_flags, de)

        return {
            "ticker": ticker,
            "red_flags": [{"key": k, "description": d} for k, d in red_flags],
            "risk_score": risk_score,
            "risk_label": (
                "Low Risk" if risk_score <= self.rules.risk_label_low_max
                else "Moderate Risk" if risk_score <= self.rules.risk_label_moderate_max
                else "High Risk"
            ),
        }
