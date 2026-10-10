from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"
DEFAULT_DB_FILE = BACKEND_DIR / "hype_tracker.db"
DEFAULT_DATABASE_URL = f"sqlite+aiosqlite:///{DEFAULT_DB_FILE.as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DATABASE_URL: str = DEFAULT_DATABASE_URL
    SERPAPI_KEY: str = ""
    ALPHA_VANTAGE_KEY: str = ""
    ENVIRONMENT: str = "development"

    JWT_SECRET: str = ""
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080

    RATE_LIMIT_LIVE_PER_MINUTE: int = 5

    SENTRY_DSN: str = ""

    # "lexicon" is dependency-free.
    # "finbert" uses a classifier trained on financial headlines.
    SENTIMENT_MODEL: str = "lexicon"

    # Absolute divergence gap that triggers a watchlist alert.
    ALERT_DIVERGENCE_THRESHOLD: float = 40.0

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def normalize_database_url(cls, value: str) -> str:
        if not value:
            return DEFAULT_DATABASE_URL

        if value.startswith("sqlite+aiosqlite:///"):
            path_part = value.replace("sqlite+aiosqlite:///", "", 1)

            if path_part.startswith("./"):
                path_part = path_part[2:]

            if not path_part:
                return DEFAULT_DATABASE_URL

            candidate = Path(path_part)

            if not candidate.is_absolute():
                candidate = BACKEND_DIR / candidate

            return f"sqlite+aiosqlite:///{candidate.as_posix()}"

        return value


settings = Settings()