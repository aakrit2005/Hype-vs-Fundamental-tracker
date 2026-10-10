from pydantic import BaseModel, Field

from app.schemas.score import ScoreRead
from app.schemas.ticker import TickerRead


class LiveLookupRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=10)


class LiveLookupResponse(BaseModel):
    ticker: TickerRead
    score: ScoreRead