from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    # Returns the current time in UTC.
    return datetime.now(timezone.utc)


class Alert(Base):
    __tablename__ = "alerts"

    # One alert per user per ticker per day.
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "ticker_id",
            "date",
            name="uq_alerts_user_ticker_date",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )

    ticker_id: Mapped[int] = mapped_column(
        ForeignKey("tickers.id"),
        index=True,
        nullable=False,
    )

    date: Mapped[date] = mapped_column(Date, nullable=False)

    message: Mapped[str] = mapped_column(Text, nullable=False)

    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )