"""
Integration tests for SQLAlchemyOHLCRepository.

These tests run against the real test database (postgres-test on port 5433)
and verify that the SQLAlchemy adapter implements the OHLCRepository port correctly.
Each test gets an isolated transaction that is rolled back after the test.
"""
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.market.domain.models import OHLCBar
from src.market.infra.repository_impl import SQLAlchemyOHLCRepository

TICKER = "X:BTCUSD"
OTHER_TICKER = "X:ETHUSD"


def _bar(ticker: str, ts: datetime, **kwargs) -> OHLCBar:
    defaults = dict(open=100.0, high=110.0, low=90.0, close=105.0, volume=1_000.0)
    defaults.update(kwargs)
    return OHLCBar(ticker=ticker, timestamp=ts, **defaults)


# ---------------------------------------------------------------------------
# get_latest_bar
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_latest_bar_returns_none_when_empty(db_session: AsyncSession):
    repo = SQLAlchemyOHLCRepository(db_session)
    result = await repo.get_latest_bar(TICKER)
    assert result is None


@pytest.mark.asyncio
async def test_get_latest_bar_returns_most_recent(db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    bar_old = _bar(TICKER, now - timedelta(hours=2), close=50.0)
    bar_new = _bar(TICKER, now - timedelta(hours=1), close=99.0)
    db_session.add_all([bar_old, bar_new])
    await db_session.flush()

    repo = SQLAlchemyOHLCRepository(db_session)
    result = await repo.get_latest_bar(TICKER)

    assert result is not None
    assert result.close == 99.0


@pytest.mark.asyncio
async def test_get_latest_bar_ignores_other_tickers(db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    db_session.add(_bar(OTHER_TICKER, now - timedelta(hours=1), close=999.0))
    await db_session.flush()

    repo = SQLAlchemyOHLCRepository(db_session)
    result = await repo.get_latest_bar(TICKER)

    assert result is None


# ---------------------------------------------------------------------------
# get_bars
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_bars_returns_empty_when_no_data(db_session: AsyncSession):
    repo = SQLAlchemyOHLCRepository(db_session)
    result = await repo.get_bars(TICKER, limit=10)
    assert result == []


@pytest.mark.asyncio
async def test_get_bars_respects_limit(db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    db_session.add_all([
        _bar(TICKER, now - timedelta(hours=3)),
        _bar(TICKER, now - timedelta(hours=2)),
        _bar(TICKER, now - timedelta(hours=1)),
    ])
    await db_session.flush()

    repo = SQLAlchemyOHLCRepository(db_session)
    result = await repo.get_bars(TICKER, limit=2)

    assert len(result) == 2


@pytest.mark.asyncio
async def test_get_bars_returned_in_descending_order(db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    db_session.add_all([
        _bar(TICKER, now - timedelta(hours=3), close=10.0),
        _bar(TICKER, now - timedelta(hours=2), close=20.0),
        _bar(TICKER, now - timedelta(hours=1), close=30.0),
    ])
    await db_session.flush()

    repo = SQLAlchemyOHLCRepository(db_session)
    result = await repo.get_bars(TICKER, limit=10)

    closes = [b.close for b in result]
    assert closes == [30.0, 20.0, 10.0]


# ---------------------------------------------------------------------------
# get_bars_since
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_bars_since_filters_by_timestamp(db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=5)

    bar_before = _bar(TICKER, now - timedelta(hours=10), close=1.0)
    bar_after_a = _bar(TICKER, now - timedelta(hours=4), close=2.0)
    bar_after_b = _bar(TICKER, now - timedelta(hours=1), close=3.0)
    db_session.add_all([bar_before, bar_after_a, bar_after_b])
    await db_session.flush()

    repo = SQLAlchemyOHLCRepository(db_session)
    result = await repo.get_bars_since(TICKER, cutoff)

    assert len(result) == 2
    closes = [b.close for b in result]
    assert closes == [2.0, 3.0]  # ascending order


@pytest.mark.asyncio
async def test_get_bars_since_returns_empty_when_all_before_cutoff(db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    db_session.add(_bar(TICKER, now - timedelta(hours=10)))
    await db_session.flush()

    repo = SQLAlchemyOHLCRepository(db_session)
    result = await repo.get_bars_since(TICKER, now - timedelta(hours=5))

    assert result == []


# ---------------------------------------------------------------------------
# get_ticker_status
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_ticker_status_returns_zeros_when_empty(db_session: AsyncSession):
    repo = SQLAlchemyOHLCRepository(db_session)
    count, earliest, latest = await repo.get_ticker_status(TICKER)
    assert count == 0
    assert earliest is None
    assert latest is None


@pytest.mark.asyncio
async def test_get_ticker_status_aggregates_correctly(db_session: AsyncSession):
    now = datetime.now(timezone.utc)
    ts_old = now - timedelta(hours=5)
    ts_new = now - timedelta(hours=1)
    db_session.add_all([
        _bar(TICKER, ts_old),
        _bar(TICKER, now - timedelta(hours=3)),
        _bar(TICKER, ts_new),
    ])
    await db_session.flush()

    repo = SQLAlchemyOHLCRepository(db_session)
    count, earliest, latest = await repo.get_ticker_status(TICKER)

    assert count == 3
    assert earliest is not None
    assert latest is not None
    assert earliest < latest
