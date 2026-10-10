from datetime import datetime, timedelta, timezone

import bcrypt
import jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    # Converts a plain password into a secure hash.
    return bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")


def verify_password(password: str, hashed_password: str) -> bool:
    # Checks whether the plain password matches the stored hash.
    return bcrypt.checkpw(
        password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def get_jwt_secret() -> str:
    # The JWT secret must exist before tokens can be created or verified.
    if not settings.JWT_SECRET:
        raise RuntimeError("JWT_SECRET is not configured.")

    return settings.JWT_SECRET


def create_access_token(user_id: int) -> str:
    # Creates a signed JWT for an authenticated user.
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
    }

    return jwt.encode(
        payload,
        get_jwt_secret(),
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    # Verifies a JWT and returns its payload.
    return jwt.decode(
        token,
        get_jwt_secret(),
        algorithms=[settings.JWT_ALGORITHM],
    )