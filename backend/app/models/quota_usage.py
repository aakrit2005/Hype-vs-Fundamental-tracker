from datetime import date

from sqlalchemy import Date, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class QuotaUsage(Base):
    __tablename__ = "quota_usage"

    # One quota counter per API per day.
    __table_args__ = (
        UniqueConstraint(
            "api_name",
            "date",
            name="uq_quota_usage_api_date",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    api_name: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
    )

    date: Mapped[date] = mapped_column(
        Date,
        index=True,
        nullable=False,
    )

    calls_made: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )