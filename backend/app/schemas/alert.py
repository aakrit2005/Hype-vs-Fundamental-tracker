from datetime import date, datetime

from pydantic import BaseModel


class AlertRead(BaseModel):
    id: int
    ticker_id: int
    symbol: str
    date: date
    message: str
    is_read: bool
    created_at: datetime