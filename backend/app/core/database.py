from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# The engine opens database connections.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
)


# The session factory gives each request its own database session.
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Base is the parent class for all SQLAlchemy models.
class Base(DeclarativeBase):
    pass


async def get_db():
    # FastAPI uses this function to inject a database session into endpoints.
    async with AsyncSessionLocal() as session:
        yield session