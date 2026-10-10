import asyncio
import logging
from datetime import date

from sqlalchemy import select

from app.core.database import AsyncSessionLocal, Base, engine

# Importing app.models registers all tables with SQLAlchemy.
import app.models  # noqa: F401

from app.models.ticker import Ticker
from app.services.ingestion import ingest_ticker_signals
from app.services.scoring.engine import calculate_scores_for_date


logger = logging.getLogger("hype_tracker.jobs")


async def run_daily_update() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    target_date = date.today()

    async with AsyncSessionLocal() as session:
        stmt = select(Ticker).where(Ticker.is_active.is_(True))
        result = await session.execute(stmt)
        tickers = result.scalars().all()

        logger.info("daily update started for %s tickers", len(tickers))

        for ticker in tickers:
            try:
                await ingest_ticker_signals(ticker.symbol, session)

            except Exception:
                # One failing ticker must not stop the rest of the run.
                logger.exception("ingestion failed for %s", ticker.symbol)

            # Small pause reduces pressure on external APIs.
            await asyncio.sleep(1)

        score_count = await calculate_scores_for_date(session, target_date)

        logger.info("scores calculated for %s tickers", score_count)


if __name__ == "__main__":
    asyncio.run(run_daily_update())