"""SQLAlchemy ORM models for all database tables."""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, Enum, Float,
    ForeignKey, Integer, JSON, String, Text,
)
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


class Base(DeclarativeBase):
    pass


class Exchange(str, enum.Enum):
    NSE = "NSE"
    BSE = "BSE"


class OrderSide(str, enum.Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, enum.Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    SL = "SL"
    SL_M = "SL-M"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"
    COMPLETE = "COMPLETE"


class StockCategory(str, enum.Enum):
    LONG_TERM_COMPOUNDER = "long_term_compounder"
    UNDERVALUED_VALUE = "undervalued_value"
    TURNAROUND = "turnaround"
    DIVIDEND_INCOME = "dividend_income"
    MOMENTUM_RISKY = "momentum_risky"
    AVOID_WATCHLIST = "avoid_watchlist"


class FinalRating(str, enum.Enum):
    STRONG_RESEARCH_CANDIDATE = "Strong Research Candidate"
    WATCH = "Watch"
    AVOID = "Avoid"


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True)
    ticker = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    sector = Column(String(100))
    industry = Column(String(100))
    exchange = Column(Enum(Exchange), nullable=False)
    isin = Column(String(12), unique=True)
    market_cap_cr = Column(Float)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    prices = relationship("DailyPrice", back_populates="stock")
    financials = relationship("FinancialStatement", back_populates="stock")
    reports = relationship("ResearchReport", back_populates="stock")


class DailyPrice(Base):
    __tablename__ = "prices"

    id = Column(BigInteger, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger)
    source = Column(String(50))

    stock = relationship("Stock", back_populates="prices")


class FinancialStatement(Base):
    __tablename__ = "financials"

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    period = Column(String(10), nullable=False)  # e.g., "Q3FY25", "FY24"
    period_type = Column(String(10), nullable=False)  # "quarterly" or "annual"
    revenue_cr = Column(Float)
    ebitda_cr = Column(Float)
    net_profit_cr = Column(Float)
    total_debt_cr = Column(Float)
    total_equity_cr = Column(Float)
    cash_cr = Column(Float)
    capex_cr = Column(Float)
    free_cash_flow_cr = Column(Float)
    roe = Column(Float)
    roce = Column(Float)
    debt_equity = Column(Float)
    interest_coverage = Column(Float)
    promoter_holding_pct = Column(Float)
    promoter_pledge_pct = Column(Float)
    source_url = Column(Text)
    fetched_at = Column(DateTime, default=datetime.utcnow)

    stock = relationship("Stock", back_populates="financials")


class ResearchReport(Base):
    __tablename__ = "research_reports"

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False, index=True)
    generated_at = Column(DateTime, default=datetime.utcnow, index=True)

    # scores
    financial_strength_score = Column(Float)
    growth_score = Column(Float)
    valuation_score = Column(Float)
    moat_score = Column(Float)
    risk_score = Column(Float)
    confidence_pct = Column(Float)

    # classification
    category = Column(Enum(StockCategory))
    final_rating = Column(Enum(FinalRating))

    # narrative fields
    business_summary = Column(Text)
    bull_case = Column(Text)
    bear_case = Column(Text)
    red_flags = Column(JSON)
    news_sentiment = Column(String(50))
    ideal_investor_type = Column(String(200))
    sources = Column(JSON)

    # ratios snapshot
    pe_ratio = Column(Float)
    pb_ratio = Column(Float)
    ev_ebitda = Column(Float)
    peg_ratio = Column(Float)
    dividend_yield = Column(Float)
    dcf_intrinsic_value = Column(Float)
    margin_of_safety_pct = Column(Float)

    disclaimer = Column(Text, default=(
        "This is educational research, not financial advice. "
        "Consult a SEBI-registered investment adviser before investing."
    ))

    stock = relationship("Stock", back_populates="reports")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    side = Column(Enum(OrderSide), nullable=False)
    order_type = Column(Enum(OrderType), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float)
    trigger_price = Column(Float)
    is_paper_trade = Column(Boolean, nullable=False, default=True)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    broker_order_id = Column(String(100))
    rationale = Column(Text)
    confirmed_by_user = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(100), unique=True, nullable=False)
    risk_appetite = Column(String(20))  # conservative / moderate / aggressive
    investment_horizon_years = Column(Integer)
    monthly_income_band = Column(String(50))
    emergency_fund_months = Column(Integer)
    existing_holdings = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
