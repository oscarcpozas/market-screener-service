import logging

import httpx

from src.config import get_settings
from src.market.constants import LIMIT, MULTIPLIER, TIMESPAN

logger = logging.getLogger(__name__)


async def fetch_ohlc_bars(
    ticker: str,
    from_ts: str,
    to_ts: str,
    http_client: httpx.AsyncClient,
) -> list[dict]:
    massive_base_url = get_settings().massive_base_url
    if not massive_base_url:
        raise RuntimeError("MASSIVE_BASE_URL is required for market data sync")

    api_key = get_settings().massive_api_key
    if not api_key:
        raise RuntimeError("MASSIVE_API_KEY is required for market data sync")

    all_results: list[dict] = []
    url: str | None = (
        f"{massive_base_url}/v2/aggs/ticker/{ticker}/range/{MULTIPLIER}/{TIMESPAN}"
        f"/{from_ts}/{to_ts}"
    )
    params: dict | None = {
        "adjusted": "true",
        "sort": "asc",
        "limit": LIMIT,
        "apiKey": api_key,
    }

    while url:
        resp = await http_client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

        results = data.get("results") or []
        all_results.extend(results)
        logger.info(
            "Fetched %d bars for %s (total so far: %d)",
            len(results),
            ticker,
            len(all_results),
        )

        next_url = data.get("next_url")
        if next_url:
            # next_url is a full URL; append apiKey
            url = next_url
            params = {"apiKey": api_key}
        else:
            url = None

    return all_results
