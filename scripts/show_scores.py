import asyncio
import sys
from datetime import date, datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = BASE_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from sqlalchemy import select

from app.core.database import AsyncSessionLocal, Base, engine

# Importing app.models registers all tables with SQLAlchemy.
import app.models

from app.models.score import Score
from app.models.ticker import Ticker


def get_target_date() -> date:
    if len(sys.argv) > 1:
        try:
            return datetime.strptime(sys.argv[1], "%Y-%m-%d").date()

        except ValueError:
            print("Date format must be YYYY-MM-DD.")
            sys.exit(1)

    return date.today()


async def ensure_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    target_date = get_target_date()

    await ensure_tables()

    async with AsyncSessionLocal() as session:
        stmt = (
            select(Ticker.symbol, Score)
            .join(Score, Score.ticker_id == Ticker.id)
            .where(Score.date == target_date)
        )

        result = await session.execute(stmt)
        rows = result.all()

        if not rows:
            print(f"No scores found for {target_date}.")
            return

        print(f"Scores for {target_date}")
        print("-" * 80)

        for symbol, score in rows:
            print(
                f"{symbol:<6} "
                f"hype={score.hype_score:<10} "
                f"fund={score.fund_score:<10} "
                f"gap={score.divergence_gap:<10} "
                f"confidence={score.confidence_flag}"
            )


if __name__ == "__main__":
    asyncio.run(main())