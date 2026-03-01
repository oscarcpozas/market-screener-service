import asyncio
import logging
from datetime import datetime, timedelta, timezone

import httpx
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from src.core.database import async_session
from src.market.client import fetch_ohlc_bars
from src.market.constants import (
    INITIAL_LOOKBACK_DAYS,
    INSERT_CHUNK_SIZE,
    PAUSE_BETWEEN_TICKERS,
    TICKERS,
)
from src.market.domain.models import OHLCBar
from src.market.domain.repository import OHLCRepository
from src.market.infra.schemas import AssetDetails

logger = logging.getLogger(__name__)


def _epoch_ms_to_utc(ms: int) -> datetime:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)


async def _get_last_timestamp(ticker: str) -> datetime | None:
    async with async_session() as session:
        result = await session.execute(
            select(func.max(OHLCBar.timestamp)).where(OHLCBar.ticker == ticker)
        )
        return result.scalar_one_or_none()


async def _bulk_upsert(rows: list[dict]) -> int:
    """Insert rows with ON CONFLICT DO NOTHING. Returns inserted count."""
    if not rows:
        return 0

    inserted = 0
    async with async_session() as session:
        for i in range(0, len(rows), INSERT_CHUNK_SIZE):
            chunk = rows[i : i + INSERT_CHUNK_SIZE]
            stmt = (
                pg_insert(OHLCBar)
                .values(chunk)
                .on_conflict_do_nothing(constraint="uq_ticker_timestamp")
            )
            result = await session.execute(stmt)
            inserted += result.rowcount
        await session.commit()
    return inserted


async def sync_ticker(ticker: str, http_client: httpx.AsyncClient) -> int:
    """Sync a single ticker. Returns number of new rows inserted."""
    last_ts = await _get_last_timestamp(ticker)

    if last_ts is None:
        # Initial load: last N days
        from_dt = datetime.now(timezone.utc) - timedelta(days=INITIAL_LOOKBACK_DAYS)
        logger.info("Initial load for %s from %s", ticker, from_dt.date())
    else:
        from_dt = last_ts + timedelta(minutes=1)

    from_ms = str(int(from_dt.timestamp() * 1000))
    to_ms = str(int(datetime.now(timezone.utc).timestamp() * 1000))

    raw_bars = await fetch_ohlc_bars(ticker, from_ms, to_ms, http_client)

    rows = [
        {
            "ticker": ticker,
            "timestamp": _epoch_ms_to_utc(bar["t"]),
            "open": bar["o"],
            "high": bar["h"],
            "low": bar["l"],
            "close": bar["c"],
            "volume": bar["v"],
            "vwap": bar.get("vw"),
            "num_trades": bar.get("n"),
        }
        for bar in raw_bars
    ]

    inserted = await _bulk_upsert(rows)
    logger.info("Inserted %d new bars for %s", inserted, ticker)
    return inserted


async def get_asset_details(ticker: str, repo: OHLCRepository) -> AssetDetails | None:
    latest = await repo.get_latest_bar(ticker)
    if latest is None:
        return None

    since = datetime.now(timezone.utc) - timedelta(hours=24)
    bars_24h = await repo.get_bars_since(ticker, since)

    if bars_24h:
        open_24h = bars_24h[0].open
        high_24h = max(b.high for b in bars_24h)
        low_24h = min(b.low for b in bars_24h)
        volume_24h = sum(b.volume for b in bars_24h)
    else:
        open_24h = latest.open
        high_24h = latest.high
        low_24h = latest.low
        volume_24h = latest.volume

    price = latest.close
    change_24h = price - open_24h
    change_pct_24h = (change_24h / open_24h * 100) if open_24h != 0 else 0.0

    return AssetDetails(
        ticker=ticker,
        price=price,
        timestamp=latest.timestamp,
        open_24h=open_24h,
        high_24h=high_24h,
        low_24h=low_24h,
        volume_24h=volume_24h,
        change_24h=change_24h,
        change_pct_24h=change_pct_24h,
    )


async def sync_all_tickers() -> dict[str, int]:
    """Sync all tickers sequentially with rate-limit pauses."""
    results: dict[str, int] = {}
    async with httpx.AsyncClient(timeout=60) as http_client:
        for i, ticker in enumerate(TICKERS):
            try:
                count = await sync_ticker(ticker, http_client)
                results[ticker] = count
            except Exception:
                logger.exception("Failed to sync %s", ticker)
                results[ticker] = -1

            # Pause between tickers to respect rate limit (skip after last)
            if i < len(TICKERS) - 1:
                logger.debug("Pausing %ds for rate limit...", PAUSE_BETWEEN_TICKERS)
                await asyncio.sleep(PAUSE_BETWEEN_TICKERS)

    return results
