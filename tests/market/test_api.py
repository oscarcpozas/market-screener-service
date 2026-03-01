from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.market.constants import TICKERS
from src.market.domain.models import OHLCBar

KNOWN_TICKER = "X:BTCUSD"


def _bar(ticker: str, ts: datetime, **kwargs) -> OHLCBar:
    defaults = dict(open=100.0, high=110.0, low=90.0, close=105.0, volume=1_000.0)
    defaults.update(kwargs)
    return OHLCBar(ticker=ticker, timestamp=ts, **defaults)


# ---------------------------------------------------------------------------
# GET /market/tickers
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_tickers(client: AsyncClient):
    response = await client.get("/market/tickers")
    assert response.status_code == 200
    assert response.json() == TICKERS


# ---------------------------------------------------------------------------
# GET /market/bars/{ticker}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_bars_returns_empty_list_when_no_data(client: AsyncClient):
    response = await client.get(f"/market/bars/{KNOWN_TICKER}")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_get_bars_returns_bars(client: AsyncClient, db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    bars = [
        _bar(KNOWN_TICKER, now - timedelta(hours=2), close=100.0),
        _bar(KNOWN_TICKER, now - timedelta(hours=1), close=200.0),
    ]
    db_session.add_all(bars)
    await db_session.flush()

    response = await client.get(f"/market/bars/{KNOWN_TICKER}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["ticker"] == KNOWN_TICKER
    assert "close" in data[0]


@pytest.mark.asyncio
async def test_get_bars_respects_limit(client: AsyncClient, db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    db_session.add_all([
        _bar(KNOWN_TICKER, now - timedelta(hours=3)),
        _bar(KNOWN_TICKER, now - timedelta(hours=2)),
        _bar(KNOWN_TICKER, now - timedelta(hours=1)),
    ])
    await db_session.flush()

    response = await client.get(f"/market/bars/{KNOWN_TICKER}?limit=1")
    assert response.status_code == 200
    assert len(response.json()) == 1


@pytest.mark.asyncio
async def test_get_bars_returned_in_descending_order(client: AsyncClient, db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    bar_old = _bar(KNOWN_TICKER, now - timedelta(hours=2), close=50.0)
    bar_new = _bar(KNOWN_TICKER, now - timedelta(hours=1), close=99.0)
    db_session.add_all([bar_old, bar_new])
    await db_session.flush()

    response = await client.get(f"/market/bars/{KNOWN_TICKER}")
    data = response.json()
    assert data[0]["close"] == 99.0  # newest first
    assert data[1]["close"] == 50.0


# ---------------------------------------------------------------------------
# GET /market/status
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sync_status_all_zeros_when_no_data(client: AsyncClient):
    response = await client.get("/market/status")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == len(TICKERS)
    for entry in data:
        assert entry["bar_count"] == 0
        assert entry["earliest"] is None
        assert entry["latest"] is None


@pytest.mark.asyncio
async def test_sync_status_reflects_inserted_bars(client: AsyncClient, db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    ts_old = now - timedelta(hours=5)
    ts_new = now - timedelta(hours=1)
    db_session.add_all([
        _bar(KNOWN_TICKER, ts_old),
        _bar(KNOWN_TICKER, ts_new),
    ])
    await db_session.flush()

    response = await client.get("/market/status")
    assert response.status_code == 200
    data = response.json()

    btc_status = next(e for e in data if e["ticker"] == KNOWN_TICKER)
    assert btc_status["bar_count"] == 2
    assert btc_status["earliest"] is not None
    assert btc_status["latest"] is not None
