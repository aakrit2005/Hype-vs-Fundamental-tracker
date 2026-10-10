from datetime import date
from typing import Optional

from sqlalchemy import Date, Float, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    # Storing raw articles lets us rescore sentiment later
    # without paying SerpAPI again.
    __table_args__ = (
        UniqueConstraint(
            "ticker_id",
            "date",
            "url",
            name="uq_news_articles_ticker_date_url",
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

    title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    snippet: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)

    # Null urls are allowed for articles without a link.
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    sentiment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)