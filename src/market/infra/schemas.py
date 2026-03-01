from datetime import datetime

from pydantic import BaseModel


class OHLCBarOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    ticker: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: float | None
    num_trades: int | None


class TickerStatus(BaseModel):
    ticker: str
    bar_count: int
    earliest: datetime | None
    latest: datetime | None


class AssetDetails(BaseModel):
    ticker: str
    price: float
    timestamp: datetime
    open_24h: float
    high_24h: float
    low_24h: float
    volume_24h: float
    change_24h: float
    change_pct_24h: float
