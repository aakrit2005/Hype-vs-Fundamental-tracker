from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import rate_limit_live
from app.core.database import get_db
from app.models.score import Score
from app.models.ticker import Ticker
from app.schemas.score import ScoreWithSymbol
from app.schemas.signals import LiveLookupRequest, LiveLookupResponse
from app.services.ingestion import ensure_ticker_exists, ingest_ticker_signals
from app.services.scoring.engine import calculate_scores_for_date

router = APIRouter(prefix="/signals", tags=["signals"])


@router.get("/leaderboard", response_model=list[ScoreWithSymbol])
async def get_divergence_leaderboard(
    limit: int = Query(default=20, ge=1, le=100),
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Score, Ticker)
        .join(Ticker, Score.ticker_id == Ticker.id)
        .where(Score.divergence_gap.is_not(None))
        .order_by(Score.date.desc())
    )

    result = await session.execute(stmt)
    rows = result.all()

    latest_by_ticker = {}

    # Keeps only the newest score for each ticker.
    for score, ticker in rows:
        if score.ticker_id not in latest_by_ticker:
            latest_by_ticker[score.ticker_id] = (score, ticker)

    latest_scores = list(latest_by_ticker.values())

    # Sorts by the size of the divergence gap.
    latest_scores.sort(
        key=lambda item: abs(item[0].divergence_gap or 0.0),
        reverse=True,
    )

    response = []

    for score, ticker in latest_scores[:limit]:
        response.append(
            {
                "id": score.id,
                "ticker_id": ticker.id,
                "symbol": ticker.symbol,
                "date": score.date,
                "hype_score": score.hype_score,
                "fund_score": score.fund_score,
                "divergence_gap": score.divergence_gap,
                "confidence_flag": score.confidence_flag,
            }
        )

    return response


@router.post(
    "/live",
    response_model=LiveLookupResponse,
    dependencies=[Depends(rate_limit_live)],
)
async def live_lookup(
    payload: LiveLookupRequest,
    session: AsyncSession = Depends(get_db),
):
    symbol = payload.symbol.upper().strip()

    try:
        ticker = await ensure_ticker_exists(session, symbol)
        await ingest_ticker_signals(symbol, session)

    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Data ingestion failed: {error!s}",
        )

    target_date = date.today()

    await calculate_scores_for_date(session, target_date)

    stmt = select(Score).where(
        Score.ticker_id == ticker.id,
        Score.date == target_date,
    )

    result = await session.execute(stmt)
    score = result.scalar_one_or_none()

    if score is None:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Score could not be generated.",
        )

    return {
        "ticker": ticker,
        "score": score,
    }