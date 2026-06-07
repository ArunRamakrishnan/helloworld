"""Risk Agent — detects red flags and computes a risk score."""
from typing import Any, Dict, List, Optional, Tuple

from src.utils.logger import get_logger
from src.utils.validators import validate_score

logger = get_logger(__name__)


RED_FLAG_DEFINITIONS = {
    "high_debt": "Debt/Equity ratio > 2.0",
    "negative_fcf": "Free cash flow is negative",
    "falling_margins": "EBITDA margin declined 3+ consecutive quarters",
    "high_promoter_pledge": "Promoter pledge > 30% of holding",
    "low_promoter_holding": "Promoter holding < 35%",
    "auditor_change": "Auditor resigned or changed in last 2 years",
    "related_party_transactions": "Significant related-party transactions flagged",
    "sudden_price_spike": "Stock price spiked > 50% in 30 days without fundamental reason",
    "negative_cash_flow_ops": "Operating cash flow is negative",
    "overvalued_pe": "PE ratio > 60",
    "high_capex_low_return": "Capex-to-revenue > 20% with ROCE < 10%",
    "governance_issue": "Governance issue detected (SEBI action, penalty, regulatory notice)",
}


class RiskAgent:
    """
    Checks for red flags and scores risk (0 = safest, 10 = most risky).
    Lower risk score is better for investment.
    """

    def detect_red_flags(self, data: Dict[str, Any]) -> List[Tuple[str, str]]:
        """
        Returns a list of (flag_key, description) tuples for each detected red flag.
        """
        flags = []

        de = data.get("debt_equity")
        if de is not None and de > 2.0:
            flags.append(("high_debt", RED_FLAG_DEFINITIONS["high_debt"]))

        fcf = data.get("fcf_cr")
        if fcf is not None and fcf < 0:
            flags.append(("negative_fcf", RED_FLAG_DEFINITIONS["negative_fcf"]))

        op_cf = data.get("operating_cash_flow_cr")
        if op_cf is not None and op_cf < 0:
            flags.append(("negative_cash_flow_ops", RED_FLAG_DEFINITIONS["negative_cash_flow_ops"]))

        pledge = data.get("promoter_pledge_pct")
        if pledge is not None and pledge > 30:
            flags.append(("high_promoter_pledge", RED_FLAG_DEFINITIONS["high_promoter_pledge"]))

        promoter_holding = data.get("promoter_holding_pct")
        if promoter_holding is not None and promoter_holding < 35:
            flags.append(("low_promoter_holding", RED_FLAG_DEFINITIONS["low_promoter_holding"]))

        pe = data.get("pe_ratio")
        if pe is not None and pe > 60:
            flags.append(("overvalued_pe", RED_FLAG_DEFINITIONS["overvalued_pe"]))

        if data.get("auditor_changed", False):
            flags.append(("auditor_change", RED_FLAG_DEFINITIONS["auditor_change"]))

        if data.get("governance_issue", False):
            flags.append(("governance_issue", RED_FLAG_DEFINITIONS["governance_issue"]))

        if data.get("sudden_price_spike", False):
            flags.append(("sudden_price_spike", RED_FLAG_DEFINITIONS["sudden_price_spike"]))

        logger.info("Red flags detected for %s: %s", data.get("ticker", "?"), [f[0] for f in flags])
        return flags

    def compute_risk_score(self, red_flags: List[Tuple[str, str]], de: Optional[float]) -> float:
        """
        Risk score from 0 (no risk) to 10 (extremely risky).
        Note: for investment decisions, lower risk score is BETTER.
        Each flag adds to risk score; severe flags add more.
        """
        severe_flags = {"high_debt", "negative_fcf", "governance_issue", "high_promoter_pledge"}
        score = 0.0
        for flag_key, _ in red_flags:
            score += 2.0 if flag_key in severe_flags else 1.0

        # Additional debt-level penalty
        if de is not None:
            if de > 3.0:
                score += 2.0
            elif de > 2.0:
                score += 1.0

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
                "Low Risk" if risk_score <= 2
                else "Moderate Risk" if risk_score <= 5
                else "High Risk"
            ),
        }
