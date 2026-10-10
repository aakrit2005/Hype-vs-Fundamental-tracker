import asyncio
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = BASE_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.database import AsyncSessionLocal
from app.services.ingestion import ingest_ticker_signals

# Fetch for a subset of MVP tickers to test the pipeline.
TEST_TICKERS = ["AAPL", "TSLA", "NVDA"]

async def run_ingestion():
    async with AsyncSessionLocal() as session:
        for symbol in TEST_TICKERS:
            print(f"--- Fetching data for {symbol} ---")
            try:
                await ingest_ticker_signals(symbol, session)
            except Exception as e:
                # If one API fails (like a bad key or timeout), we log it and keep going.
                print(f"Failed to fetch {symbol}: {e}")

if __name__ == "__main__":
    asyncio.run(run_ingestion())