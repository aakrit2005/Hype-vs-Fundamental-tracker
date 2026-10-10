import asyncio
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = BASE_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from app.core.database import AsyncSessionLocal, Base, engine

# Importing app.models registers all tables with SQLAlchemy.
import app.models

from app.services.backtest.signal import run_backtest


async def ensure_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def format_number(value) -> str:
    if value is None:
        return "n/a"

    return f"{value:.4f}"


def print_result(result) -> None:
    print("-" * 80)
    print(f"Horizon: {result.horizon_days} trading days")
    print(f"Run date: {result.run_date}")
    print(f"Sample size: {result.sample_size}")
    print(f"Information coefficient: {format_number(result.information_coefficient)}")
    print(f"Pearson correlation: {format_number(result.pearson_correlation)}")
    print(f"Average forward return: {format_number(result.avg_forward_return)}")
    print(f"Positive gap count: {result.positive_gap_count}")
    print(f"Negative gap count: {result.negative_gap_count}")
    print(
        "Avg forward return for positive gap: "
        f"{format_number(result.avg_positive_gap_forward_return)}"
    )
    print(
        "Avg forward return for negative gap: "
        f"{format_number(result.avg_negative_gap_forward_return)}"
    )

    if result.notes:
        print(f"Notes: {result.notes}")


async def main() -> None:
    await ensure_tables()

    async with AsyncSessionLocal() as session:
        for horizon in [5, 20]:
            result = await run_backtest(
                session,
                horizon_days=horizon,
                min_confidence=0.0,
            )

            print_result(result)


if __name__ == "__main__":
    asyncio.run(main())