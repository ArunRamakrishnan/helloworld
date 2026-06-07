"""API routes for the Investment Research Wizard."""
import threading
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.agents.orchestrator import Orchestrator
from src.agents.broker_agent import BrokerAgent, OrderRequest
from src.agents.portfolio_agent import PortfolioAgent
from src.agents.fisher_agent import PhilipFisherAgent
from src.agents.sentiment_agent import SentimentAgent
from src.agents.unicorn_detector import UnicornDetectorAgent
from src.agents.daily_report import DailyReportOrchestrator
from src.agents.universe_scan import UniverseScanOrchestrator
from src.api import job_store
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


# ------------------------------------------------------------------
# Philip Fisher endpoint
# ------------------------------------------------------------------

class FisherRequest(BaseModel):
    ticker: str
    business_description: str = Field(..., min_length=20)
    revenue_cagr_3y: Optional[float] = None
    profit_cagr_3y: Optional[float] = None
    roe: Optional[float] = None


@router.post("/research/fisher/{ticker}", summary="Philip Fisher analysis — innovation, vision, 10x potential")
def fisher_analysis(ticker: str, body: FisherRequest) -> Dict[str, Any]:
    try:
        agent = PhilipFisherAgent(config=cfg)
        return agent.analyze(
            ticker=ticker,
            business_description=body.business_description,
            revenue_cagr=body.revenue_cagr_3y,
            profit_cagr=body.profit_cagr_3y,
            roe=body.roe,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Fisher analysis failed for %s: %s", ticker, exc)
        raise HTTPException(status_code=500, detail="Fisher analysis failed")


# ------------------------------------------------------------------
# Sentiment endpoint
# ------------------------------------------------------------------

@router.get("/research/sentiment/{ticker}", summary="Market sentiment from public RSS feeds + LLM")
def sentiment_analysis(ticker: str) -> Dict[str, Any]:
    try:
        agent = SentimentAgent(config=cfg)
        return agent.analyze(ticker=ticker)
    except Exception as exc:
        logger.error("Sentiment analysis failed for %s: %s", ticker, exc)
        raise HTTPException(status_code=500, detail="Sentiment analysis failed")


# ------------------------------------------------------------------
# Unicorn Detector endpoint
# ------------------------------------------------------------------

class UnicornRequest(BaseModel):
    ticker: str
    business_description: str = Field(..., min_length=20)
    market_cap_cr: float = Field(..., gt=0)
    revenue_cagr_3y: Optional[float] = None
    profit_cagr_3y: Optional[float] = None
    roe: Optional[float] = None
    debt_equity: Optional[float] = None
    promoter_holding_pct: Optional[float] = None


@router.post("/research/unicorn/{ticker}", summary="Unicorn detection — small cap, founder-led, emerging themes")
def unicorn_analysis(ticker: str, body: UnicornRequest) -> Dict[str, Any]:
    try:
        agent = UnicornDetectorAgent(config=cfg)
        return agent.analyze(
            ticker=ticker,
            business_description=body.business_description,
            market_cap_cr=body.market_cap_cr,
            revenue_cagr=body.revenue_cagr_3y,
            profit_cagr=body.profit_cagr_3y,
            roe=body.roe,
            debt_equity=body.debt_equity,
            promoter_holding_pct=body.promoter_holding_pct,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Unicorn analysis failed for %s: %s", ticker, exc)
        raise HTTPException(status_code=500, detail="Unicorn analysis failed")


# ------------------------------------------------------------------
# Daily Morning Report endpoint
# ------------------------------------------------------------------

class WatchlistItem(BaseModel):
    ticker: str
    current_price: float = Field(..., gt=0)
    market_cap_cr: float = Field(..., gt=0)
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


class DailyReportRequest(BaseModel):
    watchlist: List[WatchlistItem] = Field(..., min_length=1)


@router.post("/report/daily", summary="Morning report — Top 3 per category across your watchlist")
def daily_report(body: DailyReportRequest) -> Dict[str, Any]:
    """
    Runs full research pipeline on all stocks in the watchlist and returns
    ranked picks: Top Buffett, Growth, Small Cap, Emerging Theme, Dividend,
    Fisher stocks + Stocks to Avoid + rebalancing note.
    """
    try:
        orchestrator = DailyReportOrchestrator(config=cfg)
        watchlist = [item.model_dump() for item in body.watchlist]
        return orchestrator.run(watchlist)
    except Exception as exc:
        logger.error("Daily report failed: %s", exc)
        raise HTTPException(status_code=500, detail="Daily report generation failed")


# ------------------------------------------------------------------
# Universe Scan endpoints (async — NSE/BSE full scan)
# ------------------------------------------------------------------

class UniverseScanRequest(BaseModel):
    symbol_list: Optional[List[str]] = Field(
        None,
        description="Override list of NSE symbols. If omitted, fetches from NSE API (NIFTY 500).",
    )
    stage1_top_n: int = Field(
        100,
        ge=10,
        le=500,
        description="How many candidates to pass Stage 1 screening. Default: 100.",
    )
    stage2_top_n: int = Field(
        50,
        ge=5,
        le=200,
        description="How many to run the full 9-agent pipeline on. Lower = faster. Default: 50.",
    )


def _run_scan_background(job_id: str, request_params: Dict[str, Any]):
    """Background thread worker for universe scan."""
    job_store.start_job(job_id)
    try:
        scanner = UniverseScanOrchestrator(config=cfg)

        def progress(stage, done, total, message=""):
            job_store.update_progress(job_id, stage, done, total, message)

        result = scanner.run(
            symbol_list=request_params.get("symbol_list"),
            stage1_top_n=request_params.get("stage1_top_n", 100),
            stage2_top_n=request_params.get("stage2_top_n", 50),
            progress_callback=progress,
        )
        job_store.complete_job(job_id, result)
        logger.info("Universe scan job %s complete", job_id)
    except Exception as exc:
        logger.error("Universe scan job %s failed: %s", job_id, exc)
        job_store.fail_job(job_id, str(exc))


@router.post(
    "/scan/universe",
    summary="Start a full NSE/BSE universe scan (async) — returns job_id to poll",
)
def start_universe_scan(body: UniverseScanRequest) -> Dict[str, Any]:
    """
    Kicks off a full two-stage universe scan in the background.

    Stage 1: Fast quantitative screener across NSE universe (rule-based, no LLM).
    Stage 2: Full 9-agent research pipeline on top candidates.
    Output: Top 10 per category — Buffett, Lynch, Fisher, Growth, Small Cap,
            Emerging Themes, Dividend, Stocks to Avoid.

    Returns a job_id immediately. Poll GET /scan/universe/{job_id} for results.
    Typical duration: 10-45 minutes depending on stage2_top_n and LLM availability.
    """
    params = body.model_dump()
    job_id = job_store.create_job(job_type="universe_scan", params={
        "stage1_top_n": params["stage1_top_n"],
        "stage2_top_n": params["stage2_top_n"],
        "symbol_count": len(params.get("symbol_list") or []),
    })

    thread = threading.Thread(
        target=_run_scan_background,
        args=(job_id, params),
        daemon=True,
        name=f"scan-{job_id[:8]}",
    )
    thread.start()

    return {
        "job_id": job_id,
        "status": "pending",
        "message": (
            f"Scan started. Stage 1 will screen the NSE universe, "
            f"Stage 2 will deeply analyse top {params['stage2_top_n']} candidates. "
            f"Poll GET /api/v1/scan/universe/{job_id} for progress and results."
        ),
        "poll_url": f"/api/v1/scan/universe/{job_id}",
    }


@router.get(
    "/scan/universe/{job_id}",
    summary="Get universe scan job status and results",
)
def get_universe_scan(job_id: str) -> Dict[str, Any]:
    """
    Poll this endpoint after starting a scan with POST /scan/universe.

    Response includes:
    - status: pending | running | complete | failed
    - progress: stage, done/total, pct, message
    - result: full scan report (only when status=complete)
    """
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    response: Dict[str, Any] = {
        "job_id": job["job_id"],
        "status": job["status"],
        "created_at": job["created_at"],
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at"),
        "progress": job["progress"],
    }

    if job["status"] == "failed":
        response["error"] = job.get("error")
    elif job["status"] == "complete":
        response["result"] = job["result"]

    return response


@router.get(
    "/scan/jobs",
    summary="List recent universe scan jobs",
)
def list_scan_jobs(limit: int = Query(20, ge=1, le=50)) -> Dict[str, Any]:
    """Returns recent scan jobs (newest first) without the full result payload."""
    return {
        "jobs": job_store.list_jobs(limit=limit),
        "note": "Poll GET /api/v1/scan/universe/{job_id} to get full results for a completed job.",
    }
