from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.backtest_result import BacktestResult
from app.schemas.backtest import BacktestRead

router = APIRouter(prefix="/backtest", tags=["backtest"])


@router.get("/summary", response_model=list[BacktestRead])
async def get_saved_backtests(
    limit: int = Query(default=20, ge=1, le=200),
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        select(BacktestResult)
        .order_by(
            BacktestResult.run_date.desc(),
            BacktestResult.horizon_days,
        )
        .limit(limit)
    )

    result = await session.execute(stmt)
    return result.scalars().all()