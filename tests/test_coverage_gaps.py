"""
Tests targeting specific coverage gaps across:
- fundamental_agent: compute_roce, score_fcf branches, score_debt_equity branches,
  score_revenue_cagr mid-branches, profit_cagr edge cases
- valuation_agent: dividend_yield zero price, score_pe mid-ranges, score_pb mid,
  score_peg mid, score_margin_of_safety bands, dcf zero shares
- risk_agent: de > 3.0 branch in compute_risk_score
- portfolio_agent: sector cap weight clamp, weight <= 0 early break
- orchestrator: growth_score mid-range branches
- validators: validate_ratio, validate_score/price/quantity non-numeric
- routes: 500 error path, portfolio endpoint
- logger: existing-handler branch
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from src.agents.fundamental_agent import FundamentalAgent
from src.agents.valuation_agent import ValuationAgent
from src.agents.risk_agent import RiskAgent
from src.agents.portfolio_agent import PortfolioAgent
from src.agents.orchestrator import Orchestrator
from src.utils.validators import validate_ratio, validate_score, validate_price, validate_quantity
from src.utils.logger import get_logger


# ==============================================================================
# FundamentalAgent — uncovered branches
# ==============================================================================

class TestFundamentalAgentGaps:
    def setup_method(self):
        self.agent = FundamentalAgent()

    # compute_roce
    def test_compute_roce_normal(self):
        result = self.agent.compute_roce(ebit_cr=300, total_assets_cr=2000, current_liabilities_cr=500)
        assert result == pytest.approx(300 / 1500)

    def test_compute_roce_zero_capital_employed(self):
        assert self.agent.compute_roce(300, total_assets_cr=500, current_liabilities_cr=500) is None

    def test_compute_roce_negative_capital_employed(self):
        assert self.agent.compute_roce(300, total_assets_cr=400, current_liabilities_cr=600) is None

    # score_debt_equity missing branches
    def test_score_de_between_1_and_2(self):
        assert self.agent.score_debt_equity(1.5) == 4.0

    def test_score_de_between_0_and_1(self):
        assert self.agent.score_debt_equity(0.8) == 6.0

    def test_score_de_none(self):
        assert self.agent.score_debt_equity(None) == 5.0

    # score_fcf branches
    def test_score_fcf_zero_revenue(self):
        assert self.agent.score_fcf(100, 0) == 0.0

    def test_score_fcf_medium(self):
        assert self.agent.score_fcf(120, 1000) == 8.0  # ratio=0.12

    def test_score_fcf_low_positive(self):
        assert self.agent.score_fcf(30, 1000) == 4.0   # ratio=0.03

    def test_score_fcf_negative(self):
        assert self.agent.score_fcf(-100, 1000) == 1.0

    # score_revenue_cagr missing mid-branches
    def test_score_revenue_cagr_15pct(self):
        assert self.agent.score_revenue_cagr(0.17) == 8.0

    def test_score_revenue_cagr_10pct(self):
        assert self.agent.score_revenue_cagr(0.12) == 6.0

    def test_score_revenue_cagr_5pct(self):
        assert self.agent.score_revenue_cagr(0.07) == 4.0

    def test_score_revenue_cagr_low_positive(self):
        assert self.agent.score_revenue_cagr(0.02) == 2.0

    # profit_cagr edge: negative start profit
    def test_profit_cagr_negative_start_returns_none(self):
        statements = [
            {"period": "FY21", "period_type": "annual", "net_profit_cr": -50},
            {"period": "FY22", "period_type": "annual", "net_profit_cr": 100},
            {"period": "FY23", "period_type": "annual", "net_profit_cr": 120},
            {"period": "FY24", "period_type": "annual", "net_profit_cr": 150},
        ]
        assert self.agent.profit_cagr(statements) is None

    def test_revenue_cagr_insufficient_data(self):
        statements = [{"period": "FY24", "period_type": "annual", "revenue_cr": 1000}]
        assert self.agent.revenue_cagr(statements) is None

    # overall score — all None inputs
    def test_overall_score_all_none(self):
        score = self.agent.overall_financial_strength_score(None, None, None, -100, 0)
        assert 0 <= score <= 10


# ==============================================================================
# ValuationAgent — uncovered branches
# ==============================================================================

class TestValuationAgentGaps:
    def setup_method(self):
        self.agent = ValuationAgent()

    def test_dividend_yield_zero_price_returns_none(self):
        assert self.agent.dividend_yield(10, 0) is None

    def test_dividend_yield_negative_price_returns_none(self):
        assert self.agent.dividend_yield(10, -5) is None

    def test_score_pe_between_20_and_30(self):
        assert self.agent.score_pe(25) == 4.0

    def test_score_pe_between_30_and_50(self):
        assert self.agent.score_pe(40) == 2.0

    def test_score_pe_none(self):
        assert self.agent.score_pe(None) == 5.0

    def test_score_pb_between_1_and_1_5(self):
        assert self.agent.score_pb(1.3) == 8.0

    def test_score_pb_between_3_and_5(self):
        assert self.agent.score_pb(4.0) == 3.0

    def test_score_pb_none(self):
        assert self.agent.score_pb(None) == 5.0

    def test_score_peg_between_1_and_1_5(self):
        assert self.agent.score_peg(1.2) == 5.0

    def test_score_peg_between_1_5_and_2(self):
        assert self.agent.score_peg(1.8) == 3.0

    def test_score_peg_none(self):
        assert self.agent.score_peg(None) == 5.0

    def test_score_margin_of_safety_between_25_and_40(self):
        assert self.agent.score_margin_of_safety(75, 100) == 8.0   # 25% discount

    def test_score_margin_of_safety_between_10_and_25(self):
        assert self.agent.score_margin_of_safety(88, 100) == 6.0   # 12% discount

    def test_score_margin_of_safety_between_0_and_10(self):
        assert self.agent.score_margin_of_safety(95, 100) == 4.0   # 5% discount

    def test_score_margin_of_safety_none_intrinsic(self):
        assert self.agent.score_margin_of_safety(100, None) == 5.0

    def test_dcf_zero_shares_uses_default_1(self):
        result = self.agent.dcf_intrinsic_value(fcf_cr=100, shares_outstanding_cr=0)
        assert result["intrinsic_value_per_share_with_mos"] is not None


# ==============================================================================
# RiskAgent — de > 3.0 branch
# ==============================================================================

class TestRiskAgentGaps:
    def setup_method(self):
        self.agent = RiskAgent()

    def test_risk_score_de_above_3(self):
        score = self.agent.compute_risk_score([], de=3.5)
        assert score == 2.0  # extra penalty for de > 3.0

    def test_risk_score_de_between_2_and_3(self):
        score = self.agent.compute_risk_score([], de=2.5)
        assert score == 1.0  # smaller penalty

    def test_risk_score_de_none_no_extra_penalty(self):
        score = self.agent.compute_risk_score([], de=None)
        assert score == 0.0


# ==============================================================================
# PortfolioAgent — sector cap clamp and break paths
# ==============================================================================

class TestPortfolioAgentGaps:
    def setup_method(self):
        self.agent = PortfolioAgent()

    def test_sector_weight_clamped_when_sector_nearly_full(self):
        """Pack IT sector to near its 20% limit, third IT stock should be clamped."""
        profile = {
            "user_id": "u1",
            "risk_appetite": "moderate",
            "investment_horizon_years": 5,
            "emergency_fund_months": 8,
        }
        reports = [
            {"ticker": "IT1", "sector": "IT", "final_rating": "Strong Research Candidate",
             "financial_strength_score": 9, "moat_score": 9, "valuation_score": 9, "risk_score": 1},
            {"ticker": "IT2", "sector": "IT", "final_rating": "Strong Research Candidate",
             "financial_strength_score": 8, "moat_score": 8, "valuation_score": 8, "risk_score": 2},
            {"ticker": "IT3", "sector": "IT", "final_rating": "Strong Research Candidate",
             "financial_strength_score": 7, "moat_score": 7, "valuation_score": 7, "risk_score": 3},
        ]
        result = self.agent.suggest_allocation(profile, reports, 100000)
        it_total = sum(a["allocation_pct"] for a in result.get("allocations", []) if a["sector"] == "IT")
        assert it_total <= 20.01  # must not exceed sector cap

    def test_weight_zero_triggers_break(self):
        """Once sector is full, remaining stocks in same sector are skipped."""
        profile = {
            "user_id": "u1",
            "risk_appetite": "conservative",  # max 5% per stock, 15% per sector
            "investment_horizon_years": 5,
            "emergency_fund_months": 8,
        }
        reports = [
            {"ticker": f"STOCK{i}", "sector": "PHARMA", "final_rating": "Strong Research Candidate",
             "financial_strength_score": 9, "moat_score": 9, "valuation_score": 9, "risk_score": 1}
            for i in range(10)
        ]
        result = self.agent.suggest_allocation(profile, reports, 100000)
        pharma_total = sum(a["allocation_pct"] for a in result.get("allocations", []) if a["sector"] == "PHARMA")
        assert pharma_total <= 15.01


# ==============================================================================
# Orchestrator — growth score mid-range branches
# ==============================================================================

class TestOrchestratorGaps:
    def setup_method(self):
        cfg = MagicMock()
        cfg.llm.anthropic_api_key = None
        cfg.news_api_key = None
        cfg.paper_trading = True
        self.orch = Orchestrator(config=cfg)

    def test_growth_score_between_15_and_20(self):
        assert self.orch._growth_score({"revenue_cagr_3y": 0.17, "profit_cagr_3y": 0.16}) == 8.0

    def test_growth_score_between_10_and_15(self):
        assert self.orch._growth_score({"revenue_cagr_3y": 0.12, "profit_cagr_3y": 0.11}) == 6.0

    def test_growth_score_between_5_and_10(self):
        assert self.orch._growth_score({"revenue_cagr_3y": 0.07, "profit_cagr_3y": 0.06}) == 4.0

    def test_growth_score_none_values(self):
        score = self.orch._growth_score({"revenue_cagr_3y": None, "profit_cagr_3y": None})
        assert score == 2.0  # None treated as 0


# ==============================================================================
# Validators — uncovered functions / branches
# ==============================================================================

class TestValidatorGaps:
    def test_validate_ratio_none_returns_none(self):
        assert validate_ratio(None, "pe") is None

    def test_validate_ratio_valid_float(self):
        assert validate_ratio(15.5, "pe") == pytest.approx(15.5)

    def test_validate_ratio_valid_int(self):
        assert validate_ratio(10, "pb") == pytest.approx(10.0)

    def test_validate_ratio_non_numeric_raises(self):
        with pytest.raises(ValueError):
            validate_ratio("high", "pe")

    def test_validate_score_non_numeric_raises(self):
        with pytest.raises(ValueError):
            validate_score("bad", "moat")

    def test_validate_price_non_numeric_raises(self):
        with pytest.raises(ValueError):
            validate_price("expensive")

    def test_validate_quantity_float_truncated(self):
        assert validate_quantity(5.9) == 5  # int(5.9) = 5

    def test_validate_ratio_zero_valid(self):
        assert validate_ratio(0.0, "ratio") == pytest.approx(0.0)


# ==============================================================================
# FundamentalAgent — last remaining branches
# ==============================================================================

class TestFundamentalLastBranches:
    def setup_method(self):
        self.agent = FundamentalAgent()

    def test_revenue_cagr_returns_value_when_enough_data(self):
        statements = [
            {"period": "FY21", "period_type": "annual", "revenue_cr": 800},
            {"period": "FY22", "period_type": "annual", "revenue_cr": 900},
            {"period": "FY23", "period_type": "annual", "revenue_cr": 1000},
            {"period": "FY24", "period_type": "annual", "revenue_cr": 1200},
        ]
        result = self.agent.revenue_cagr(statements, years=3)
        assert result is not None and result > 0

    def test_profit_cagr_none_end_value(self):
        statements = [
            {"period": "FY21", "period_type": "annual", "net_profit_cr": 100},
            {"period": "FY22", "period_type": "annual", "net_profit_cr": 110},
            {"period": "FY23", "period_type": "annual", "net_profit_cr": 120},
            {"period": "FY24", "period_type": "annual", "net_profit_cr": None},
        ]
        assert self.agent.profit_cagr(statements) is None

    def test_profit_cagr_valid_returns_value(self):
        statements = [
            {"period": "FY21", "period_type": "annual", "net_profit_cr": 100},
            {"period": "FY22", "period_type": "annual", "net_profit_cr": 115},
            {"period": "FY23", "period_type": "annual", "net_profit_cr": 130},
            {"period": "FY24", "period_type": "annual", "net_profit_cr": 150},
        ]
        result = self.agent.profit_cagr(statements, years=3)
        assert result is not None and result > 0

    def test_score_roe_between_10_and_15(self):
        assert self.agent.score_roe(0.12) == 4.0

    def test_score_fcf_between_5_and_10(self):
        assert self.agent.score_fcf(80, 1000) == 6.0  # ratio=0.08


# ==============================================================================
# ValuationAgent — last remaining branches
# ==============================================================================

class TestValuationLastBranches:
    def setup_method(self):
        self.agent = ValuationAgent()

    def test_score_pe_between_15_and_20(self):
        assert self.agent.score_pe(17) == 6.0

    def test_score_pb_between_1_5_and_3(self):
        assert self.agent.score_pb(2.0) == 5.0

    def test_score_pb_at_or_below_1(self):
        assert self.agent.score_pb(0.9) == 10.0


# ==============================================================================
# DataCollector — fetch_historical_prices general exception path
# ==============================================================================

class TestDataCollectorLastBranches:
    def test_fetch_historical_prices_general_exception_returns_empty(self):
        from datetime import date
        import sys
        # Provide a mock yfinance that raises a generic exception (not ImportError)
        mock_yf = MagicMock()
        mock_yf.download.side_effect = RuntimeError("download failed")
        sys.modules["yfinance"] = mock_yf

        cfg = MagicMock()
        cfg.news_api_key = None
        from src.agents.data_collector import DataCollectorAgent
        agent = DataCollectorAgent(config=cfg)
        result = agent.fetch_historical_prices("RELIANCE", date(2024, 1, 1))
        assert result == []

        del sys.modules["yfinance"]


# ==============================================================================
# Logger — existing-handler branch (get_logger called twice for same name)
# ==============================================================================

class TestLoggerGaps:
    def test_get_logger_returns_same_instance_on_repeat_call(self):
        logger1 = get_logger("test.repeat.logger")
        logger2 = get_logger("test.repeat.logger")  # hits the "if logger.handlers: return" branch
        assert logger1 is logger2

    def test_get_logger_custom_level(self):
        logger = get_logger("test.level.debug", level="DEBUG")
        import logging
        assert logger.level == logging.DEBUG


# ==============================================================================
# API routes — 500 error path and portfolio endpoint
# ==============================================================================

from src.api.main import app
client = TestClient(app)


class TestAPIRoutesGaps:
    def test_research_500_on_unexpected_error(self):
        with patch("src.api.routes.Orchestrator") as mock_cls:
            mock_cls.return_value.research.side_effect = RuntimeError("unexpected")
            resp = client.post("/api/v1/research/TCS", json={
                "ticker": "TCS",
                "current_price": 3500.0,
                "market_cap_cr": 1270000,
                "business_description": "TCS is a global IT services and consulting company.",
                "statements": [],
            })
        assert resp.status_code == 500

    def test_portfolio_suggest_endpoint(self):
        payload = {
            "user_profile": {
                "user_id": "test",
                "risk_appetite": "moderate",
                "investment_horizon_years": 5,
                "emergency_fund_months": 8,
            },
            "research_reports": [],
        }
        resp = client.post(
            "/api/v1/portfolio/suggest",
            json=payload,
            params={"total_investment": 100000},
        )
        assert resp.status_code == 200
        assert "disclaimer" in resp.json()

    def test_research_400_on_value_error(self):
        with patch("src.api.routes.Orchestrator") as mock_cls:
            mock_cls.return_value.research.side_effect = ValueError("bad ticker")
            resp = client.post("/api/v1/research/BAD", json={
                "ticker": "BAD",
                "current_price": 100.0,
                "market_cap_cr": 1000,
                "business_description": "Some company doing something interesting.",
                "statements": [],
            })
        assert resp.status_code == 400
