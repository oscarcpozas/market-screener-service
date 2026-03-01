import asyncio
import logging

from src.core.database import dispose_engine
from src.market.domain.service import sync_all_tickers
from src.core.worker import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="market.sync_ohlc")
def sync_ohlc() -> dict[str, int]:
    async def _run() -> dict[str, int]:
        try:
            results = await sync_all_tickers()
            total = sum(v for v in results.values() if v > 0)
            logger.info("OHLC sync complete — %d new bars total", total)
            return results
        finally:
            # Must dispose before the event loop closes — asyncpg connections
            # are bound to the loop and cannot be reused across asyncio.run() calls.
            await dispose_engine()

    return asyncio.run(_run())
