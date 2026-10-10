from pydantic import BaseModel, Field


class WatchlistCreate(BaseModel):
    ticker_id: int = Field(gt=0)