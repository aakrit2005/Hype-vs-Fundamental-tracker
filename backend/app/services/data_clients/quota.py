from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quota_usage import QuotaUsage


async def increment_quota(session: AsyncSession, api_name: str):
    today = date.today()
    
    # Look for today's usage record for this specific API.
    stmt = select(QuotaUsage).where(
        QuotaUsage.api_name == api_name,
        QuotaUsage.date == today
    )
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()
    
    if record:
        # If it exists, just add 1 to the counter.
        record.calls_made += 1
    else:
        # If it doesn't exist, create the first record for today.
        record = QuotaUsage(api_name=api_name, date=today, calls_made=1)
        session.add(record)
        
    # Save the change to the database immediately so we don't lose track.
    await session.commit()