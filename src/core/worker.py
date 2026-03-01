from celery import Celery

from src.config import get_settings

celery_app = Celery(
    "crypto-screener",
    broker=get_settings().redis_url,
    backend=get_settings().redis_url,
    include=["src.market.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    beat_schedule={
        "sync-ohlc": {
            "task": "market.sync_ohlc",
            "schedule": 600.0,  # every 10 minutes
        },
    },
)
