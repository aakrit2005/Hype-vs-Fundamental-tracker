from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.alert import Alert
from app.models.ticker import Ticker
from app.models.user import User
from app.schemas.alert import AlertRead


router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertRead])
async def list_alerts(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Alert, Ticker.symbol)
        .join(Ticker, Alert.ticker_id == Ticker.id)
        .where(Alert.user_id == current_user.id)
        .order_by(Alert.date.desc(), Alert.created_at.desc())
    )

    result = await session.execute(stmt)
    rows = result.all()

    response = []

    for alert, symbol in rows:
        response.append(
            {
                "id": alert.id,
                "ticker_id": alert.ticker_id,
                "symbol": symbol,
                "date": alert.date,
                "message": alert.message,
                "is_read": alert.is_read,
                "created_at": alert.created_at,
            }
        )

    return response


@router.post("/{alert_id}/read", response_model=AlertRead)
async def mark_alert_read(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    alert = await session.get(Alert, alert_id)

    if alert is None or alert.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found.",
        )

    alert.is_read = True
    await session.commit()

    ticker = await session.get(Ticker, alert.ticker_id)

    return {
        "id": alert.id,
        "ticker_id": alert.ticker_id,
        "symbol": ticker.symbol if ticker else "",
        "date": alert.date,
        "message": alert.message,
        "is_read": alert.is_read,
        "created_at": alert.created_at,
    }