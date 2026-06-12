"""Shared yfinance fetch helper with rate limiting.

Yahoo Finance allows roughly 2 requests/second before issuing 429s.
This module enforces a global minimum gap between requests and retries
on 429 with exponential backoff.
"""
import threading
import time
from typing import Any, Dict, Optional

from src.utils.logger import get_logger

logger = get_logger(__name__)

# Global rate-limit state — shared across all threads / agent instances
_lock = threading.Lock()
_last_request_time: float = 0.0

MIN_GAP_SECONDS = 0.6    # max ~1.6 req/s — safely under Yahoo's limit
MAX_RETRIES = 4


def fetch_ticker_info(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Fetch yfinance .info for one NSE symbol with global rate limiting + retry.

    Rate limiter ensures at least MIN_GAP_SECONDS between any two requests
    across all threads, preventing Yahoo Finance 429s.
    """
    global _last_request_time

    ns_symbol = f"{symbol}.NS"

    for attempt in range(MAX_RETRIES):
        # Enforce minimum gap between requests (global across all threads)
        with _lock:
            now = time.monotonic()
            elapsed = now - _last_request_time
            if elapsed < MIN_GAP_SECONDS:
                time.sleep(MIN_GAP_SECONDS - elapsed)
            _last_request_time = time.monotonic()

        try:
            import yfinance as yf
            info = yf.Ticker(ns_symbol).info
            if not info or info.get("regularMarketPrice") is None:
                return None
            return info
        except Exception as exc:
            msg = str(exc)
            if "429" in msg or "Too Many Requests" in msg:
                wait = 2 ** attempt   # 1s, 2s, 4s, 8s
                logger.warning("429 rate-limit for %s — backing off %ds (attempt %d/%d)",
                               symbol, wait, attempt + 1, MAX_RETRIES)
                time.sleep(wait)
            else:
                logger.debug("yfinance fetch failed for %s: %s", symbol, exc)
                return None

    logger.warning("Giving up on %s after %d attempts", symbol, MAX_RETRIES)
    return None
