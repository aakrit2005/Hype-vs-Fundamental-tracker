from datetime import date

from pydantic import BaseModel


class ScoreRead(BaseModel):
    id: int
    ticker_id: int
    date: date
    hype_score: float | None = None
    fund_score: float | None = None
    divergence_gap: float | None = None
    confidence_flag: float | None = None


class ScoreWithSymbol(BaseModel):
    id: int
    ticker_id: int
    symbol: str
    date: date
    hype_score: float | None = None
    fund_score: float | None = None
    divergence_gap: float | None = None
    confidence_flag: float | None = None