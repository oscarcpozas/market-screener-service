from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Float, Index, Integer, String, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class OHLCBar(Base):
    __tablename__ = "ohlc_bar"
    __table_args__ = (
        UniqueConstraint("ticker", "timestamp", name="uq_ticker_timestamp"),
        Index(
            "ix_ticker_timestamp_desc",
            "ticker",
            text("timestamp DESC"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(20), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    vwap: Mapped[float | None] = mapped_column(Float, nullable=True)
    num_trades: Mapped[int | None] = mapped_column(Integer, nullable=True)
