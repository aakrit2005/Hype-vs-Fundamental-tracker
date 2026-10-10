from datetime import date

from sqlalchemy import Date, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Score(Base):
    __tablename__ = "scores"

    # One derived score row per ticker per day.
    # This keeps the derived score history stable and idempotent.
    __table_args__ = (
        UniqueConstraint(
            "ticker_id",
            "date",
            name="uq_scores_ticker_date",
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

    hype_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    fund_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # divergence_gap is the main signal.
    divergence_gap: Mapped[float | None] = mapped_column(Float, nullable=True)

    # confidence_flag lowers trust for thin data.
    confidence_flag: Mapped[float | None] = mapped_column(Float, nullable=True)