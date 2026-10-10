from datetime import date

from sqlalchemy import Date, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class RawSignal(Base):
    __tablename__ = "raw_signals"

    # One raw signal row per ticker per day.
    # This prevents duplicate ingestion when a fetch job is rerun.
    __table_args__ = (
        UniqueConstraint(
            "ticker_id",
            "date",
            name="uq_raw_signals_ticker_date",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    ticker_id: Mapped[int] = mapped_column(
        ForeignKey("tickers.id"),
        index=True,
        nullable=False,
    )

    date: Mapped[date] = mapped_column(
        Date,
        index=True,
        nullable=False,
    )

    # Hype inputs.
    trends_volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    news_volume: Mapped[int | None] = mapped_column(Integer, nullable=True)
    news_sentiment: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Fundamental inputs.
    pe_ratio: Mapped[float | None] = mapped_column(Float, nullable=True)
    eps_growth: Mapped[float | None] = mapped_column(Float, nullable=True)