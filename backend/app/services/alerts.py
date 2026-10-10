from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.alert import Alert
from app.models.score import Score
from app.models.ticker import Ticker
from app.models.watchlist import Watchlist


async def evaluate_alerts(
    session: AsyncSession,
    target_date: date,
    threshold: float | None = None,
    min_confidence: float = 0.5,
) -> int:
    # Checks every watched ticker for a divergence large enough to notify.
    if threshold is None:
        threshold = settings.ALERT_DIVERGENCE_THRESHOLD

    stmt = (
        select(Watchlist.user_id, Watchlist.ticker_id, Ticker.symbol)
        .join(Ticker, Watchlist.ticker_id == Ticker.id)
    )

    result = await session.execute(stmt)
    watched = result.all()

    created = 0

    for user_id, ticker_id, symbol in watched:
        score_stmt = select(Score).where(
            Score.ticker_id == ticker_id,
            Score.date == target_date,
        )

        score_result = await session.execute(score_stmt)
        score = score_result.scalar_one_or_none()

        if score is None or score.divergence_gap is None:
            continue

        # Low-confidence scores must not trigger notifications.
        if (score.confidence_flag or 0.0) < min_confidence:
            continue

        if abs(score.divergence_gap) < threshold:
            continue

        existing_stmt = select(Alert).where(
            Alert.user_id == user_id,
            Alert.ticker_id == ticker_id,
            Alert.date == target_date,
        )

        existing_result = await session.execute(existing_stmt)

        if existing_result.scalar_one_or_none() is not None:
            continue

        if score.divergence_gap > 0:
            direction = "overhyped relative to fundamentals"
        else:
            direction = "underhyped relative to fundamentals"

        message = (
            f"{symbol} divergence gap {score.divergence_gap:.1f} "
            f"on {target_date}: {direction}"
        )

        session.add(
            Alert(
                user_id=user_id,
                ticker_id=ticker_id,
                date=target_date,
                message=message,
            )
        )

        created += 1

    await session.commit()

    return created