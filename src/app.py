import logging

from fastapi import FastAPI

from src.config import get_settings
from src.market.api.router import router as market_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

app = FastAPI(title=get_settings().project_name)
app.include_router(market_router)


@app.get("/")
async def read_root():
    return {"status": "ok"}
