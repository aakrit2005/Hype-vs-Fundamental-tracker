from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.ticker import Ticker
from app.models.user import User
from app.models.watchlist import Watchlist
from app.schemas.ticker import TickerRead
from app.schemas.watchlist import WatchlistCreate

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("", response_model=list[TickerRead])
async def get_watchlist(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Ticker)
        .join(Watchlist, Watchlist.ticker_id == Ticker.id)
        .where(Watchlist.user_id == current_user.id)
        .order_by(Ticker.symbol)
    )

    result = await session.execute(stmt)
    return result.scalars().all()


@router.post("", response_model=TickerRead, status_code=status.HTTP_201_CREATED)
async def add_to_watchlist(
    payload: WatchlistCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    ticker = await session.get(Ticker, payload.ticker_id)

    if ticker is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticker not found.",
        )

    stmt = select(Watchlist).where(
        Watchlist.user_id == current_user.id,
        Watchlist.ticker_id == ticker.id,
    )

    result = await session.execute(stmt)
    existing = result.scalar_one_or_none()

    if existing is None:
        session.add(
            Watchlist(
                user_id=current_user.id,
                ticker_id=ticker.id,
            )
        )

        await session.commit()

    return ticker


@router.delete("/{ticker_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_watchlist(
    ticker_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    stmt = select(Watchlist).where(
        Watchlist.user_id == current_user.id,
        Watchlist.ticker_id == ticker_id,
    )

    result = await session.execute(stmt)
    entry = result.scalar_one_or_none()

    if entry is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Watchlist entry not found.",
        )

    await session.delete(entry)
    await session.commit()

