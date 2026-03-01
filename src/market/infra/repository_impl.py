from datetime import datetime

from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from src.market.domain.models import OHLCBar
from src.market.domain.repository import OHLCRepository


class SQLAlchemyOHLCRepository(OHLCRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest_bar(self, ticker: str) -> OHLCBar | None:
        result = await self._session.execute(
            select(OHLCBar)
            .where(OHLCBar.ticker == ticker)
            .order_by(OHLCBar.timestamp.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_bars(self, ticker: str, limit: int) -> list[OHLCBar]:
        result = await self._session.execute(
            select(OHLCBar)
            .where(OHLCBar.ticker == ticker)
            .order_by(OHLCBar.timestamp.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_bars_since(self, ticker: str, since: datetime) -> list[OHLCBar]:
        result = await self._session.execute(
            select(OHLCBar)
            .where(OHLCBar.ticker == ticker, OHLCBar.timestamp >= since)
            .order_by(OHLCBar.timestamp.asc())
        )
        return list(result.scalars().all())

    async def get_ticker_status(
            self, ticker: str
    ) -> tuple[int, datetime | None, datetime | None]:
        result = await self._session.execute(
            select(
                func.count(OHLCBar.id),
                func.min(OHLCBar.timestamp),
                func.max(OHLCBar.timestamp),
            )
            .where(OHLCBar.ticker == ticker)
        )
        count, earliest, latest = result.one()
        return count, earliest, latest


async def get_ohlc_repository(
        session: AsyncSession = Depends(get_db_session),
) -> OHLCRepository:
    return SQLAlchemyOHLCRepository(session)
