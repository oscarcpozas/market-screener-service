from fastapi import APIRouter, Depends, HTTPException, Query

from src.market.constants import TICKERS
from src.market.domain.repository import OHLCRepository
from src.market.infra.repository_impl import get_ohlc_repository
from src.market.infra.schemas import AssetDetails, OHLCBarOut, TickerStatus
from src.market.domain.service import get_asset_details

router = APIRouter(prefix="/market", tags=["market"])


@router.get("/tickers")
async def list_tickers() -> list[str]:
    return TICKERS


@router.get("/bars/{ticker:path}", response_model=list[OHLCBarOut])
async def get_bars(
        ticker: str,
        limit: int = Query(default=100, ge=1, le=5000),
        repo: OHLCRepository = Depends(get_ohlc_repository),
) -> list[OHLCBarOut]:
    bars = await repo.get_bars(ticker, limit)
    return [OHLCBarOut.model_validate(bar) for bar in bars]


@router.get("/assets/{ticker:path}", response_model=AssetDetails)
async def asset_details(
        ticker: str,
        repo: OHLCRepository = Depends(get_ohlc_repository),
) -> AssetDetails:
    if ticker not in TICKERS:
        raise HTTPException(status_code=404, detail="Ticker not found")
    details = await get_asset_details(ticker, repo)
    if details is None:
        raise HTTPException(status_code=404, detail="No data for ticker")
    return details


@router.get("/status", response_model=list[TickerStatus])
async def sync_status(
        repo: OHLCRepository = Depends(get_ohlc_repository),
) -> list[TickerStatus]:
    statuses: list[TickerStatus] = []
    for ticker in TICKERS:
        count, earliest, latest = await repo.get_ticker_status(ticker)
        statuses.append(
            TickerStatus(ticker=ticker, bar_count=count, earliest=earliest, latest=latest)
        )
    return statuses
