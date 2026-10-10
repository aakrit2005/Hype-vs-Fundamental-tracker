from datetime import date

from sqlalchemy import Date, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PriceBar(Base):
    __tablename__ = "price_bars"

    # One price row per ticker per day.
    # This prevents duplicate price history rows.
    __table_args__ = (
        UniqueConstraint(
            "ticker_id",
            "date",
            name="uq_price_bars_ticker_date",
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

    # Adjusted close is preferred because it handles splits and dividends.
    close_price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )