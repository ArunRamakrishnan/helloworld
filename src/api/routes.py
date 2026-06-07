"""API routes for the Investment Research Wizard."""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.agents.orchestrator import Orchestrator
from src.agents.broker_agent import BrokerAgent, OrderRequest
from src.agents.portfolio_agent import PortfolioAgent
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()
cfg = get_config()

DISCLAIMER = (
    "This is educational research, not financial advice. "
    "Consult a SEBI-registered investment adviser before investing."
)


# ------------------------------------------------------------------
# Request/Response models
# ------------------------------------------------------------------

class ResearchRequest(BaseModel):
    ticker: str = Field(..., json_schema_extra={"example": "RELIANCE"})
    current_price: float = Field(..., gt=0, json_schema_extra={"example": 2850.50})
    market_cap_cr: float = Field(..., gt=0, json_schema_extra={"example": 1930000})
    business_description: str = Field(..., min_length=20)
    eps: Optional[float] = None
    book_value_per_share: Optional[float] = None
    debt_cr: float = 0.0
    cash_cr: float = 0.0
    ebitda_cr: float = 0.0
    fcf_cr: float = 0.0
    shares_outstanding_cr: float = 1.0
    dividend_per_share: float = 0.0
    statements: List[Dict[str, Any]] = Field(default_factory=list)


class OrderRequestModel(BaseModel):
    ticker: str
    side: str = Field(..., pattern="^(BUY|SELL)$")
    quantity: int = Field(..., gt=0)
    price: Optional[float] = Field(None, gt=0)
    order_type: str = Field("LIMIT", pattern="^(LIMIT|MARKET|SL|SL-M)$")
    rationale: str = ""
    user_confirmed: bool = False
    available_funds: Optional[float] = None


class UserProfileModel(BaseModel):
    user_id: str
    risk_appetite: str = Field(..., pattern="^(conservative|moderate|aggressive)$")
    investment_horizon_years: int = Field(..., gt=0)
    emergency_fund_months: int = Field(default=0)
    monthly_income_band: Optional[str] = None
    existing_holdings: Optional[List[Dict]] = None


# ------------------------------------------------------------------
# Research endpoints
# ------------------------------------------------------------------

@router.post("/research/{ticker}", summary="Run full research analysis on a stock")
def research_stock(ticker: str, body: ResearchRequest) -> Dict[str, Any]:
    """
    Runs all agents (fundamental, valuation, moat, risk, news) and returns
    a structured research report with scores, rating, and disclaimer.
    """
    try:
        orchestrator = Orchestrator(config=cfg)
        report = orchestrator.research(
            ticker=ticker,
            current_price=body.current_price,
            market_cap_cr=body.market_cap_cr,
            statements=body.statements,
            business_description=body.business_description,
            eps=body.eps,
            book_value_per_share=body.book_value_per_share,
            debt_cr=body.debt_cr,
            cash_cr=body.cash_cr,
            ebitda_cr=body.ebitda_cr,
            fcf_cr=body.fcf_cr,
            shares_outstanding_cr=body.shares_outstanding_cr,
            dividend_per_share=body.dividend_per_share,
        )
        return report
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Research failed for %s: %s", ticker, exc)
        raise HTTPException(status_code=500, detail="Research pipeline failed")


# ------------------------------------------------------------------
# Order endpoints
# ------------------------------------------------------------------

@router.post("/orders/preview", summary="Preview an order without executing it")
def preview_order(body: OrderRequestModel) -> Dict[str, Any]:
    req = OrderRequest(body.ticker, body.side, body.quantity, body.price, body.order_type, body.rationale)
    agent = BrokerAgent(config=cfg)
    return agent.preview_order(req)


@router.post("/orders/place", summary="Place a paper or live order (requires user_confirmed=true)")
def place_order(body: OrderRequestModel) -> Dict[str, Any]:
    req = OrderRequest(body.ticker, body.side, body.quantity, body.price, body.order_type, body.rationale)
    agent = BrokerAgent(config=cfg)
    return agent.place_order(req, user_confirmed=body.user_confirmed, available_funds=body.available_funds)


@router.get("/orders/paper-log", summary="Get paper trading order log")
def get_paper_log() -> Dict[str, Any]:
    agent = BrokerAgent(config=cfg)
    return {"orders": agent.get_paper_trade_log(), "disclaimer": DISCLAIMER}


# ------------------------------------------------------------------
# Portfolio endpoints
# ------------------------------------------------------------------

class PortfolioRequest(BaseModel):
    user_profile: UserProfileModel
    research_reports: List[Dict[str, Any]] = []


@router.post("/portfolio/suggest", summary="Suggest allocation bands based on user profile")
def suggest_portfolio(
    body: PortfolioRequest,
    total_investment: float = Query(..., gt=0, description="Total amount to invest in INR"),
) -> Dict[str, Any]:
    agent = PortfolioAgent()
    profile_dict = body.user_profile.model_dump()
    return agent.suggest_allocation(profile_dict, body.research_reports, total_investment)


# ------------------------------------------------------------------
# Info endpoints
# ------------------------------------------------------------------

@router.get("/categories", summary="List all stock categories")
def list_categories() -> Dict[str, Any]:
    return {
        "categories": [
            {"id": "long_term_compounder", "name": "Long-term Compounders", "description": "High-quality businesses with durable moats"},
            {"id": "undervalued_value", "name": "Undervalued Value Stocks", "description": "Trading below intrinsic value"},
            {"id": "turnaround", "name": "Turnaround Candidates", "description": "Recovering from temporary difficulties"},
            {"id": "dividend_income", "name": "Dividend / Income Stocks", "description": "Steady dividend payers"},
            {"id": "momentum_risky", "name": "Momentum (Risky)", "description": "Strong momentum but elevated risk"},
            {"id": "avoid_watchlist", "name": "Avoid / Watchlist", "description": "Red flags present — monitor only"},
        ],
        "disclaimer": DISCLAIMER,
    }


@router.get("/disclaimer")
def get_disclaimer() -> Dict[str, str]:
    return {"disclaimer": DISCLAIMER}
