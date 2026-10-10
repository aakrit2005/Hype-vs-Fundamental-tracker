import asyncio
import sys
from datetime import date
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = BASE_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from sqlalchemy import select

from app.core.database import AsyncSessionLocal, Base, engine

# Importing app.models registers all tables with SQLAlchemy.
import app.models

from app.models.ticker import Ticker
from app.services.alerts import evaluate_alerts
from app.services.ingestion import ingest_ticker_signals
from app.services.scoring.engine import calculate_scores_for_date


async def ensure_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    await ensure_tables()

    target_date = date.today()

    async with AsyncSessionLocal() as session:
        stmt = select(Ticker).where(Ticker.is_active == True)
        result = await session.execute(stmt)
        tickers = result.scalars().all()

        print(f"Running daily update for {target_date}.")

        for ticker in tickers:
            print(f"--- {ticker.symbol} ---")

            try:
                await ingest_ticker_signals(ticker.symbol, session)

            except Exception as error:
                print(f"Failed to ingest {ticker.symbol}: {error}")

            await asyncio.sleep(1)

        score_count = await calculate_scores_for_date(session, target_date)
        print(f"Calculated scores for {score_count} tickers.")

        alert_count = await evaluate_alerts(session, target_date)
        print(f"Created {alert_count} alerts.")


if __name__ == "__main__":
    asyncio.run(main())