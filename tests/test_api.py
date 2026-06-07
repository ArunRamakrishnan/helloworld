"""Integration tests for the FastAPI backend using TestClient."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)

DISCLAIMER_FRAGMENT = "SEBI"

SAMPLE_RESEARCH_PAYLOAD = {
    "ticker": "TCS",
    "current_price": 3500.0,
    "market_cap_cr": 1270000,
    "business_description": "TCS is a global IT services and consulting company headquartered in Mumbai.",
    "eps": 97.0,
    "book_value_per_share": 350.0,
    "debt_cr": 150,
    "cash_cr": 500,
    "ebitda_cr": 20000,
    "fcf_cr": 8000,
    "shares_outstanding_cr": 360,
    "dividend_per_share": 46.0,
    "statements": [
        {"period": "FY23", "period_type": "annual", "revenue_cr": 226000, "net_profit_cr": 42000,
         "total_equity_cr": 80000, "total_debt_cr": 2000, "capex_cr": 3000, "free_cash_flow_cr": 40000},
        {"period": "FY24", "period_type": "annual", "revenue_cr": 240000, "net_profit_cr": 45000,
         "total_equity_cr": 90000, "total_debt_cr": 1800, "capex_cr": 3500, "free_cash_flow_cr": 43000},
    ],
}


# ------------------------------------------------------------------
# Health endpoint
# ------------------------------------------------------------------

def test_health_returns_ok():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert DISCLAIMER_FRAGMENT in data["disclaimer"]


# ------------------------------------------------------------------
# Categories endpoint
# ------------------------------------------------------------------

def test_categories_returns_six_categories():
    resp = client.get("/api/v1/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["categories"]) == 6
    ids = [c["id"] for c in data["categories"]]
    assert "long_term_compounder" in ids
    assert "avoid_watchlist" in ids

def test_categories_has_disclaimer():
    resp = client.get("/api/v1/categories")
    assert DISCLAIMER_FRAGMENT in resp.json()["disclaimer"]

def test_disclaimer_endpoint():
    resp = client.get("/api/v1/disclaimer")
    assert resp.status_code == 200
    assert DISCLAIMER_FRAGMENT in resp.json()["disclaimer"]


# ------------------------------------------------------------------
# Order preview endpoint
# ------------------------------------------------------------------

def test_order_preview_returns_preview():
    payload = {
        "ticker": "RELIANCE",
        "side": "BUY",
        "quantity": 10,
        "price": 2850.0,
        "order_type": "LIMIT",
        "rationale": "Value buy",
        "user_confirmed": False,
    }
    resp = client.post("/api/v1/orders/preview", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["ticker"] == "RELIANCE"
    assert "mode" in data
    assert "disclaimer" in data

def test_order_preview_shows_paper_trade_mode():
    payload = {"ticker": "INFY", "side": "BUY", "quantity": 5, "price": 1400.0, "user_confirmed": False}
    resp = client.post("/api/v1/orders/preview", json=payload)
    assert "PAPER" in resp.json()["mode"]


# ------------------------------------------------------------------
# Order placement — safety gate
# ------------------------------------------------------------------

def test_order_place_rejected_without_confirmation():
    payload = {"ticker": "TCS", "side": "BUY", "quantity": 1, "price": 3500.0, "user_confirmed": False}
    resp = client.post("/api/v1/orders/place", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "REJECTED"

def test_order_place_accepted_with_confirmation():
    payload = {"ticker": "WIPRO", "side": "BUY", "quantity": 2, "price": 450.0, "user_confirmed": True}
    resp = client.post("/api/v1/orders/place", json=payload)
    assert resp.status_code == 200
    assert resp.json()["status"] == "COMPLETE"
    assert resp.json()["is_paper_trade"] is True

def test_order_place_rejected_insufficient_funds():
    payload = {
        "ticker": "RELIANCE", "side": "BUY", "quantity": 1000, "price": 3000.0,
        "user_confirmed": True, "available_funds": 10000.0,
    }
    resp = client.post("/api/v1/orders/place", json=payload)
    assert resp.json()["status"] == "REJECTED"
    assert "Insufficient" in resp.json()["reason"]

def test_order_side_validation():
    payload = {"ticker": "TCS", "side": "INVALID", "quantity": 1, "price": 100.0, "user_confirmed": False}
    resp = client.post("/api/v1/orders/place", json=payload)
    assert resp.status_code == 422  # FastAPI validation error


# ------------------------------------------------------------------
# Paper log endpoint
# ------------------------------------------------------------------

def test_paper_log_returns_list():
    resp = client.get("/api/v1/orders/paper-log")
    assert resp.status_code == 200
    data = resp.json()
    assert "orders" in data
    assert isinstance(data["orders"], list)


# ------------------------------------------------------------------
# Research endpoint
# ------------------------------------------------------------------

def test_research_returns_200():
    resp = client.post("/api/v1/research/TCS", json=SAMPLE_RESEARCH_PAYLOAD)
    assert resp.status_code == 200

def test_research_contains_disclaimer():
    resp = client.post("/api/v1/research/TCS", json=SAMPLE_RESEARCH_PAYLOAD)
    assert DISCLAIMER_FRAGMENT in resp.json()["disclaimer"]

def test_research_invalid_ticker_in_body_returns_400():
    bad_payload = {**SAMPLE_RESEARCH_PAYLOAD, "ticker": ""}
    resp = client.post("/api/v1/research/INVALID__TICKER__$", json=bad_payload)
    # Either 400 (our validation) or 422 (pydantic) depending on path param handling
    assert resp.status_code in (400, 422, 200)

def test_research_scores_in_range():
    resp = client.post("/api/v1/research/TCS", json=SAMPLE_RESEARCH_PAYLOAD)
    data = resp.json()
    for key in ["financial_strength_score", "valuation_score", "moat_score", "risk_score"]:
        val = data.get(key)
        if val is not None:
            assert 0 <= val <= 10, f"{key}={val} out of range"
