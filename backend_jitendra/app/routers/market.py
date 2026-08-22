"""Server-side proxy for the Binance Futures ticker used by js/market-ticker.js.

Polling Binance straight from the browser breaks wherever that host is blocked
or CORS-restricted, and it leaks a third-party call to every visitor. Proxying
here also lets one cached upstream call serve every connected client.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, Query

from ..config import settings
from ..schemas import MarketResponse, MarketTicker

router = APIRouter(prefix="/market", tags=["market"])

DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT"]

_cache: dict[str, tuple[float, MarketTicker]] = {}
_cache_lock = asyncio.Lock()


async def _fetch_ticker(client: httpx.AsyncClient, symbol: str) -> MarketTicker:
    response = await client.get(
        f"{settings.binance_base_url}/fapi/v1/ticker/24hr",
        params={"symbol": symbol},
    )
    response.raise_for_status()
    data = response.json()

    return MarketTicker(
        symbol=data["symbol"],
        last_price=float(data["lastPrice"]),
        price_change_percent=float(data["priceChangePercent"]),
        quote_volume=float(data["quoteVolume"]),
    )


@router.get("/tickers", response_model=MarketResponse)
async def get_tickers(
    symbols: str = Query(default=",".join(DEFAULT_SYMBOLS), description="Comma separated Binance symbols"),
) -> MarketResponse:
    requested = [item.strip().upper() for item in symbols.split(",") if item.strip()] or DEFAULT_SYMBOLS
    requested = requested[:10]

    now = time.monotonic()
    fresh: dict[str, MarketTicker] = {}
    missing: list[str] = []

    async with _cache_lock:
        for symbol in requested:
            cached = _cache.get(symbol)

            if cached and now - cached[0] < settings.market_cache_seconds:
                fresh[symbol] = cached[1]
            else:
                missing.append(symbol)

    detail: str | None = None

    if missing:
        try:
            timeout = httpx.Timeout(settings.market_timeout_seconds)

            async with httpx.AsyncClient(timeout=timeout) as client:
                results = await asyncio.gather(*(_fetch_ticker(client, symbol) for symbol in missing))

            async with _cache_lock:
                stamped = time.monotonic()

                for ticker in results:
                    _cache[ticker.symbol] = (stamped, ticker)
                    fresh[ticker.symbol] = ticker
        except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
            # Serving stale cache beats blanking the ticker; the frontend shows
            # "Live (unavailable)" when available is false.
            detail = f"Upstream market data unavailable: {type(exc).__name__}"

            async with _cache_lock:
                for symbol in missing:
                    cached = _cache.get(symbol)

                    if cached:
                        fresh[symbol] = cached[1]

    tickers = [fresh[symbol] for symbol in requested if symbol in fresh]

    return MarketResponse(
        available=detail is None and len(tickers) == len(requested),
        source="binance-futures",
        fetched_at=datetime.now(timezone.utc),
        tickers=tickers,
        detail=detail,
    )
