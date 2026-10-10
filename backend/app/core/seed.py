import asyncio

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, Base, engine

# Importing app.models registers all tables with SQLAlchemy.
import app.models  # noqa: F401

from app.models.ticker import Ticker


# Highly liquid, heavily discussed tickers keep the MVP dashboard meaningful.
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


async def seed() -> None:
    # create_all only creates tables that do not exist yet.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        for item in MVP_TICKERS:
            stmt = select(Ticker).where(Ticker.symbol == item["symbol"])
            result = await session.execute(stmt)

            # Existing tickers are skipped, so seeding is safe to repeat.
            if result.scalar_one_or_none() is None:
                session.add(Ticker(**item))

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())