from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.market.domain.models import OHLCBar

KNOWN_TICKER = "X:BTCUSD"
UNKNOWN_TICKER = "X:FAKEUSD"


def _bar(ticker: str, ts: datetime, **kwargs) -> OHLCBar:
    defaults = dict(open=100.0, high=110.0, low=90.0, close=105.0, volume=1000.0)
    defaults.update(kwargs)
    return OHLCBar(ticker=ticker, timestamp=ts, **defaults)


@pytest.mark.asyncio
async def test_returns_404_when_no_data(client: AsyncClient):
    response = await client.get(f"/market/assets/{KNOWN_TICKER}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_ticker_not_in_known_list_returns_404(client: AsyncClient):
    response = await client.get(f"/market/assets/{UNKNOWN_TICKER}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_returns_asset_details_with_correct_price(
        client: AsyncClient, db_session: AsyncSession
):
    now = datetime.now(timezone.utc)
    bar = _bar(KNOWN_TICKER, now - timedelta(hours=1), close=42_000.0)
    db_session.add(bar)
    await db_session.flush()

    response = await client.get(f"/market/assets/{KNOWN_TICKER}")
    assert response.status_code == 200

    data = response.json()
    assert data["ticker"] == KNOWN_TICKER
    assert data["price"] == 42_000.0


@pytest.mark.asyncio
async def test_24h_stats_computed_correctly(
        client: AsyncClient, db_session: AsyncSession
):
    now = datetime.now(timezone.utc)

    # bar_old is outside the 24h window — should NOT affect 24h stats
    bar_old = _bar(
        KNOWN_TICKER,
        now - timedelta(hours=25),
        open=50.0, high=55.0, low=45.0, close=52.0, volume=500.0,
    )
    # bar_a is the oldest bar inside the 24h window → open_24h comes from here
    bar_a = _bar(
        KNOWN_TICKER,
        now - timedelta(hours=20),
        open=100.0, high=120.0, low=90.0, close=110.0, volume=1000.0,
    )
    # bar_b is the newest bar → latest close becomes price
    bar_b = _bar(
        KNOWN_TICKER,
        now - timedelta(hours=1),
        open=115.0, high=130.0, low=105.0, close=125.0, volume=500.0,
    )

    db_session.add_all([bar_old, bar_a, bar_b])
    await db_session.flush()

    response = await client.get(f"/market/assets/{KNOWN_TICKER}")
    assert response.status_code == 200

    data = response.json()
    assert data["price"] == 125.0
    assert data["open_24h"] == 100.0  # from bar_a (oldest in window)
    assert data["high_24h"] == 130.0  # max(120, 130)
    assert data["low_24h"] == 90.0  # min(90, 105)
    assert data["volume_24h"] == 1500.0  # 1000 + 500
    assert data["change_24h"] == 25.0  # 125 - 100
    assert data["change_pct_24h"] == 25.0  # 25/100 * 100
