import asyncio
import sys
from pathlib import Path


# This finds the project root from this file's location.
BASE_DIR = Path(__file__).resolve().parents[1]

# The FastAPI app package lives inside backend/.
BACKEND_DIR = BASE_DIR / "backend"

# This makes backend/app importable from any terminal folder.
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from sqlalchemy import select

from app.core.database import AsyncSessionLocal, Base, engine

# Importing app.models registers all models with SQLAlchemy.
import app.models

from app.models.ticker import Ticker


MVP_TICKERS = [
    {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
    {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Cyclical"},
    {"symbol": "NVDA", "name": "NVIDIA Corp", "sector": "Technology"},
    {"symbol": "MSFT", "name": "Microsoft Corp", "sector": "Technology"},
    {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Cyclical"},
    {"symbol": "META", "name": "Meta Platforms", "sector": "Technology"},
    {"symbol": "AMD", "name": "Advanced Micro Devices", "sector": "Technology"},
    {"symbol": "JPM", "name": "JPMorgan Chase", "sector": "Financial Services"},
]


async def create_tables():
    # This creates tables before any insert is attempted.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed():
    await create_tables()

    async with AsyncSessionLocal() as session:
        print("Seeding database...")

        for ticker_data in MVP_TICKERS:
            # This checks for an existing ticker before inserting.
            stmt = select(Ticker).where(Ticker.symbol == ticker_data["symbol"])
            result = await session.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing is None:
                session.add(Ticker(**ticker_data))
                print(f"Added {ticker_data['symbol']}")

        await session.commit()

    await engine.dispose()

    print("Seeding complete.")


if __name__ == "__main__":
    asyncio.run(seed())