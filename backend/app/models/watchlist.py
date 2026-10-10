from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


def utc_now() -> datetime:
    # Returns the current time in UTC.
    return datetime.now(timezone.utc)


class Watchlist(Base):
    __tablename__ = "watchlists"

    # One user can only add a ticker once.
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "ticker_id",
            name="uq_watchlists_user_ticker",
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

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utc_now,
        nullable=False,
    )