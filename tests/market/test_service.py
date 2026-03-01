from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import pytest

from src.market.domain.models import OHLCBar
from src.market.domain.service import get_asset_details

TICKER = "X:BTCUSD"


def _bar(ts: datetime, **kwargs) -> OHLCBar:
    defaults = dict(open=100.0, high=110.0, low=90.0, close=105.0, volume=1_000.0)
    defaults.update(kwargs)
    return OHLCBar(ticker=TICKER, timestamp=ts, **defaults)


def _mock_repo(*, latest: OHLCBar | None, bars_since: list[OHLCBar]) -> AsyncMock:
    repo = AsyncMock()
    repo.get_latest_bar.return_value = latest
    repo.get_bars_since.return_value = bars_since
    return repo


@pytest.mark.asyncio
async def test_returns_none_when_no_latest_bar():
    repo = _mock_repo(latest=None, bars_since=[])
    result = await get_asset_details(TICKER, repo)
    assert result is None


@pytest.mark.asyncio
async def test_returns_details_with_single_bar():
    """When bars_since is empty, service falls back to the latest bar's OHLC."""
    now = datetime.now(timezone.utc)
    bar = _bar(now - timedelta(hours=1), open=200.0, high=220.0, low=195.0, close=210.0, volume=500.0)
    repo = _mock_repo(latest=bar, bars_since=[])

    result = await get_asset_details(TICKER, repo)

    assert result is not None
    assert result.ticker == TICKER
    assert result.price == 210.0
    assert result.open_24h == 200.0
    assert result.high_24h == 220.0
    assert result.low_24h == 195.0
    assert result.volume_24h == 500.0
    assert result.change_24h == 10.0
    assert result.change_pct_24h == pytest.approx(5.0)


@pytest.mark.asyncio
async def test_computes_24h_stats_from_multiple_bars():
    """Aggregates open/high/low/volume across all bars in the 24h window."""
    now = datetime.now(timezone.utc)
    bar_latest = _bar(now - timedelta(hours=1), open=115.0, high=130.0, low=105.0, close=125.0, volume=500.0)
    bar_oldest = _bar(now - timedelta(hours=20), open=100.0, high=120.0, low=90.0, close=110.0, volume=1_000.0)
    # bars_since is ordered ASC, so oldest first
    bars_since = [bar_oldest, bar_latest]
    repo = _mock_repo(latest=bar_latest, bars_since=bars_since)

    result = await get_asset_details(TICKER, repo)

    assert result is not None
    assert result.price == 125.0
    assert result.open_24h == 100.0  # open of the first bar (oldest)
    assert result.high_24h == 130.0  # max(120, 130)
    assert result.low_24h == 90.0  # min(90, 105)
    assert result.volume_24h == 1_500.0  # 1000 + 500
    assert result.change_24h == 25.0  # 125 - 100
    assert result.change_pct_24h == pytest.approx(25.0)  # 25/100 * 100


@pytest.mark.asyncio
async def test_change_pct_is_zero_when_open_is_zero():
    """Guard against division by zero when open_24h is 0."""
    now = datetime.now(timezone.utc)
    bar = _bar(now - timedelta(hours=1), open=0.0, close=50.0)
    repo = _mock_repo(latest=bar, bars_since=[bar])

    result = await get_asset_details(TICKER, repo)

    assert result is not None
    assert result.change_pct_24h == 0.0
