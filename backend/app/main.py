import logging
import time
from contextlib import asynccontextmanager
from fastapi import Depends

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine, get_db
from app.core.logging import configure_logging

# Importing app.models registers all tables with Base.metadata.
import app.models  # noqa: F401


configure_logging(settings.ENVIRONMENT)

logger = logging.getLogger("hype_tracker")

if settings.SENTRY_DSN:
    import sentry_sdk

    # Sentry captures unhandled exceptions in deployed environments.
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,
        environment=settings.ENVIRONMENT,
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Development creates tables automatically.
    # Production uses app.core.init_db before startup.
    if settings.ENVIRONMENT.lower() == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


app = FastAPI(
    title="Hype Fundamentals Tracker",
    version="0.5.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = time.perf_counter()

    response = await call_next(request)

    duration_ms = (time.perf_counter() - start) * 1000

    logger.info(
        "request completed",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration_ms, 2),
        },
    )

    return response


app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "hype-fundamentals-tracker",
        "docs": "/docs",
    }


@app.get("/healthz")
async def healthz(session: AsyncSession = Depends(get_db)):
    # Uptime monitors call this endpoint.
    await session.execute(text("SELECT 1"))

    return {"status": "ok"}