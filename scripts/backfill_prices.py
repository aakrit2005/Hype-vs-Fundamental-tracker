import asyncio
import math
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = BASE_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


import yfinance as yf
from sqlalchemy import select

from app.core.database import AsyncSessionLocal, Base, engine

# Importing app.models registers all tables with SQLAlchemy.
import app.models

from app.models.price_bar import PriceBar
from app.models.ticker import Ticker
from app.services.data_clients.quota import increment_quota


async def ensure_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def fetch_history(symbol: str):
    # yfinance is synchronous, so this function is run inside a thread pool.
    ticker = yf.Ticker(symbol)

    return ticker.history(
        period="2y",
        interval="1d",
        auto_adjust=False,
    )


async def backfill_for_ticker(session, ticker: Ticker) -> int:
    loop = asyncio.get_running_loop()

    try:
        df = await loop.run_in_executor(
            None,
            fetch_history,
            ticker.symbol,
        )

    except Exception as error:
        print(f"Failed to fetch price history for {ticker.symbol}: {error}")
        return 0

    if df is None or df.empty:
        print(f"No price history returned for {ticker.symbol}.")
        return 0

    # Track yfinance usage even though it is not directly billed.
    await increment_quota(session, "yfinance")

    stmt = select(PriceBar.date).where(PriceBar.ticker_id == ticker.id)
    result = await session.execute(stmt)
    existing_dates = set(result.scalars().all())

    added = 0

    for timestamp, row in df.iterrows():
        bar_date = timestamp.date()

        if bar_date in existing_dates:
            continue

        close_price = row.get("Adj Close")

        try:
            close_value = float(close_price)

        except (TypeError, ValueError):
            close_price = row.get("Close")

            try:
                close_value = float(close_price)

            except (TypeError, ValueError):
                continue

        if math.isnan(close_value):
            continue

        if close_value <= 0:
            continue

        session.add(
            PriceBar(
                ticker_id=ticker.id,
                date=bar_date,
                close_price=close_value,
            )
        )

        added += 1

    await session.commit()

    return added


async def main() -> None:
    await ensure_tables()

    async with AsyncSessionLocal() as session:
        stmt = select(Ticker).where(Ticker.is_active == True)
        result = await session.execute(stmt)
        tickers = result.scalars().all()

        total_added = 0

        for ticker in tickers:
            added = await backfill_for_ticker(session, ticker)
            total_added += added

            print(f"{ticker.symbol}: added {added} price bars.")

            # Small pause reduces the chance of rate limiting.
            await asyncio.sleep(1)

        print(f"Total added price bars: {total_added}")


if __name__ == "__main__":
    asyncio.run(main())