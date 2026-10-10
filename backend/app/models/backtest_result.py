from datetime import date

from sqlalchemy import Date, Float, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class BacktestResult(Base):
    __tablename__ = "backtest_results"

    id: Mapped[int] = mapped_column(primary_key=True)

    # The day the backtest was run.
    run_date: Mapped[date] = mapped_column(
        Date,
        index=True,
        nullable=False,
    )

    # Horizon is measured in trading days, not calendar days.
    horizon_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Minimum confidence required for a score to enter the backtest.
    min_confidence: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    sample_size: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Information coefficient is the rank correlation between
    # divergence gap and forward return.
    information_coefficient: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    pearson_correlation: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    avg_forward_return: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    positive_gap_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    negative_gap_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    avg_positive_gap_forward_return: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    avg_negative_gap_forward_return: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )