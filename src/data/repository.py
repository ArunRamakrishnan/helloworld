"""Data access layer — all database queries go through here."""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import create_engine, desc
from sqlalchemy.orm import Session, sessionmaker

from src.data.models import (
    Base, DailyPrice, FinancialStatement, Order, ResearchReport,
    Stock, UserProfile,
)
from src.utils.config import get_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def build_engine(url: Optional[str] = None):
    cfg = get_config()
    return create_engine(url or cfg.database.postgres_url, pool_pre_ping=True)


def create_all_tables(engine=None):
    eng = engine or build_engine()
    Base.metadata.create_all(eng)


class StockRepository:
    def __init__(self, session: Session):
        self._s = session

    def get_by_ticker(self, ticker: str) -> Optional[Stock]:
        return self._s.query(Stock).filter(Stock.ticker == ticker.upper()).first()

    def list_active(self) -> List[Stock]:
        return self._s.query(Stock).filter(Stock.is_active == True).all()

    def upsert(self, ticker: str, name: str, exchange, sector: str = None, **kwargs) -> Stock:
        stock = self.get_by_ticker(ticker)
        if stock is None:
            stock = Stock(ticker=ticker.upper(), name=name, exchange=exchange)
            self._s.add(stock)
        stock.name = name
        stock.sector = sector
        for k, v in kwargs.items():
            setattr(stock, k, v)
        stock.updated_at = datetime.utcnow()
        self._s.flush()
        return stock


class ResearchReportRepository:
    def __init__(self, session: Session):
        self._s = session

    def latest_for_stock(self, stock_id: int) -> Optional[ResearchReport]:
        return (
            self._s.query(ResearchReport)
            .filter(ResearchReport.stock_id == stock_id)
            .order_by(desc(ResearchReport.generated_at))
            .first()
        )

    def save(self, report: ResearchReport) -> ResearchReport:
        self._s.add(report)
        self._s.flush()
        return report

    def list_by_category(self, category) -> List[ResearchReport]:
        return (
            self._s.query(ResearchReport)
            .filter(ResearchReport.category == category)
            .order_by(desc(ResearchReport.generated_at))
            .all()
        )


class OrderRepository:
    def __init__(self, session: Session):
        self._s = session

    def save(self, order: Order) -> Order:
        self._s.add(order)
        self._s.flush()
        logger.info(
            "Order saved | paper=%s | side=%s | qty=%d | price=%s",
            order.is_paper_trade, order.side, order.quantity, order.price,
        )
        return order

    def list_for_stock(self, stock_id: int) -> List[Order]:
        return (
            self._s.query(Order)
            .filter(Order.stock_id == stock_id)
            .order_by(desc(Order.created_at))
            .all()
        )
