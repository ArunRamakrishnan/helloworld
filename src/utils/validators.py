"""Input validation helpers used across all agents."""
from typing import Any, Optional


def validate_ticker(ticker: str) -> str:
    """Validate and normalise an NSE/BSE ticker symbol."""
    if not ticker or not isinstance(ticker, str):
        raise ValueError("Ticker must be a non-empty string")
    cleaned = ticker.strip().upper()
    if not cleaned.replace("-", "").replace("&", "").isalnum():
        raise ValueError(f"Invalid ticker format: {ticker!r}")
    return cleaned


def validate_quantity(qty: Any) -> int:
    """Validate order quantity is a positive integer."""
    try:
        qty_int = int(qty)
    except (TypeError, ValueError):
        raise ValueError(f"Quantity must be an integer, got {qty!r}")
    if qty_int <= 0:
        raise ValueError(f"Quantity must be positive, got {qty_int}")
    return qty_int


def validate_price(price: Any) -> float:
    """Validate order price is a positive float."""
    try:
        price_float = float(price)
    except (TypeError, ValueError):
        raise ValueError(f"Price must be numeric, got {price!r}")
    if price_float <= 0:
        raise ValueError(f"Price must be positive, got {price_float}")
    return price_float


def validate_score(score: Any, name: str = "score") -> float:
    """Validate a score is within [0, 10]."""
    try:
        val = float(score)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be numeric, got {score!r}")
    if not 0 <= val <= 10:
        raise ValueError(f"{name} must be between 0 and 10, got {val}")
    return val


def validate_ratio(value: Optional[float], name: str) -> Optional[float]:
    """Return the ratio if valid (positive float or None for N/A)."""
    if value is None:
        return None
    if not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric or None")
    return float(value)
