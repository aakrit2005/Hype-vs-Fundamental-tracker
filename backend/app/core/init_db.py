import asyncio

from app.core.database import Base, engine

# Importing app.models registers every table with SQLAlchemy.
import app.models  # noqa: F401


async def create_all_tables() -> None:
    # create_all only creates tables that do not exist yet.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_all_tables())