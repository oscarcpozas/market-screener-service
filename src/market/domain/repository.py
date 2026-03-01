from abc import ABC, abstractmethod
from datetime import datetime

from src.market.domain.models import OHLCBar


class OHLCRepository(ABC):
    @abstractmethod
    async def get_latest_bar(self, ticker: str) -> OHLCBar | None: ...

    @abstractmethod
    async def get_bars(self, ticker: str, limit: int) -> list[OHLCBar]: ...

    @abstractmethod
    async def get_bars_since(self, ticker: str, since: datetime) -> list[OHLCBar]: ...

    @abstractmethod
    async def get_ticker_status(
            self, ticker: str
    ) -> tuple[int, datetime | None, datetime | None]: ...
