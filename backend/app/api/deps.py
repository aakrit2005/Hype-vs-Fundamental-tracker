from collections import defaultdict
from time import time

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

# This tells Swagger UI where to send the login form.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    # Converts a JWT into an actual user row.
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))

    except Exception:
        raise credentials_exception

    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise credentials_exception

    return user


class SimpleRateLimiter:
    def __init__(self, max_calls: int, window_seconds: int):
        # This is a fixed-window in-memory rate limiter.
        # It works well for a single-process MVP.
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self.events = defaultdict(list)

    def allow(self, key: str) -> bool:
        now = time()
        cutoff = now - self.window_seconds

        events = self.events[key]

        # Remove old events outside the current window.
        while events and events[0] <= cutoff:
            events.pop(0)

        if len(events) < self.max_calls:
            events.append(now)
            return True

        return False


live_rate_limiter = SimpleRateLimiter(
    max_calls=settings.RATE_LIMIT_LIVE_PER_MINUTE,
    window_seconds=60,
)


def rate_limit_live(request: Request) -> None:
    # Protects expensive live lookup calls from repeated use.
    key = request.client.host if request.client else "unknown"

    if not live_rate_limiter.allow(key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded.",
        )