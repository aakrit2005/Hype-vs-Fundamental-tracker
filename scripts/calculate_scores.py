import asyncio
import sys
from datetime import date, datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = BASE_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from app.core.database import AsyncSessionLocal, Base, engine

# Importing app.models registers all tables with SQLAlchemy.
import app.models

from app.services.scoring.engine import calculate_scores_for_date


def get_target_date() -> date:
    # This allows the script to calculate scores for today by default.
    # It also allows a specific date in YYYY-MM-DD format.
    if len(sys.argv) > 1:
        try:
            return datetime.strptime(sys.argv[1], "%Y-%m-%d").date()

        except ValueError:
            print("Date format must be YYYY-MM-DD.")
            sys.exit(1)

    return date.today()


async def ensure_tables() -> None:
    # This makes the script safe even if the API server has not run yet.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    target_date = get_target_date()

    await ensure_tables()

    async with AsyncSessionLocal() as session:
        count = await calculate_scores_for_date(session, target_date)

        print(f"Calculated scores for {count} tickers on {target_date}.")


if __name__ == "__main__":
    asyncio.run(main())