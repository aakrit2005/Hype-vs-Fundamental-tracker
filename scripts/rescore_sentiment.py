import asyncio
import sys
from collections import defaultdict
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = BASE_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


from sqlalchemy import select

from app.core.database import AsyncSessionLocal, Base, engine

# Importing app.models registers all tables with SQLAlchemy.
import app.models

from app.models.news_article import NewsArticle
from app.models.raw_signal import RawSignal
from app.services.scoring.engine import calculate_scores_for_date
from app.services.scoring.sentiment import get_sentiment_analyzer


async def ensure_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    await ensure_tables()

    analyzer = get_sentiment_analyzer()

    async with AsyncSessionLocal() as session:
        stmt = select(NewsArticle).order_by(
            NewsArticle.ticker_id,
            NewsArticle.date,
        )

        result = await session.execute(stmt)
        articles = result.scalars().all()

        if not articles:
            print("No stored articles found. Run daily_update first.")
            return

        groups = defaultdict(list)

        for article in articles:
            text = f"{article.title or ''} {article.snippet or ''}".strip()

            article.sentiment_score = analyzer.score(text) if text else 0.0

            groups[(article.ticker_id, article.date)].append(
                article.sentiment_score
            )

        await session.commit()

        # Rewrite the daily aggregate sentiment on raw signals.
        for (ticker_id, day), scores in groups.items():
            stmt = select(RawSignal).where(
                RawSignal.ticker_id == ticker_id,
                RawSignal.date == day,
            )

            result = await session.execute(stmt)
            raw_signal = result.scalar_one_or_none()

            if raw_signal is not None:
                raw_signal.news_sentiment = sum(scores) / len(scores)

        await session.commit()

        affected_dates = sorted({day for (_, day) in groups.keys()})

        for day in affected_dates:
            await calculate_scores_for_date(session, day)

        print(
            f"Rescored {len(articles)} articles across "
            f"{len(affected_dates)} dates using {analyzer.name}."
        )


if __name__ == "__main__":
    asyncio.run(main())