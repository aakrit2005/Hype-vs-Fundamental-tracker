from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.score import Score
from app.models.ticker import Ticker
from app.schemas.backtest import BacktestSummary
from app.schemas.score import ScoreRead
from app.schemas.ticker import TickerRead
from app.services.backtest.signal import calculate_backtest_summary_for_ticker

router = APIRouter(prefix="/tickers", tags=["tickers"])


async def get_ticker_or_404(session: AsyncSession, ticker_id: int) -> Ticker:
    ticker = await session.get(Ticker, ticker_id)

    if ticker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticker not found.",
        )

    return ticker


@router.get("", response_model=list[TickerRead])
async def list_tickers(session: AsyncSession = Depends(get_db)):
    stmt = select(Ticker).where(Ticker.is_active.is_(True)).order_by(Ticker.symbol)

    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{ticker_id}", response_model=TickerRead)
async def get_ticker(ticker_id: int, session: AsyncSession = Depends(get_db)):
    return await get_ticker_or_404(session, ticker_id)


@router.get("/{ticker_id}/score", response_model=ScoreRead)
async def get_latest_score(ticker_id: int, session: AsyncSession = Depends(get_db)):
    await get_ticker_or_404(session, ticker_id)

    stmt = (
        select(Score)
        .where(Score.ticker_id == ticker_id)
        .order_by(Score.date.desc())
        .limit(1)
    )

    result = await session.execute(stmt)
    score = result.scalar_one_or_none()

    if score is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No score found for this ticker.",
        )

    return score


@router.get("/{ticker_id}/history", response_model=list[ScoreRead])
async def get_score_history(
    ticker_id: int,
    days: int = Query(default=30, ge=1, le=3650),
    session: AsyncSession = Depends(get_db),
):
    await get_ticker_or_404(session, ticker_id)

    start_date = date.today() - timedelta(days=days)

    stmt = (
        select(Score)
        .where(
            Score.ticker_id == ticker_id,
            Score.date >= start_date,
        )
        .order_by(Score.date.desc())
    )

    result = await session.execute(stmt)
    return result.scalars().all()


@router.get("/{ticker_id}/backtest", response_model=BacktestSummary)
async def get_ticker_backtest(
    ticker_id: int,
    horizon: int = Query(default=5, ge=1, le=252),
    session: AsyncSession = Depends(get_db),
):
    await get_ticker_or_404(session, ticker_id)

    summary = await calculate_backtest_summary_for_ticker(
        session,
        ticker_id=ticker_id,
        horizon_days=horizon,
        min_confidence=0.0,
    )

    return summary