from datetime import date

from pydantic import BaseModel, ConfigDict


class BacktestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    run_date: date
    horizon_days: int
    min_confidence: float
    sample_size: int
    information_coefficient: float | None = None
    pearson_correlation: float | None = None
    avg_forward_return: float | None = None
    positive_gap_count: int
    negative_gap_count: int
    avg_positive_gap_forward_return: float | None = None
    avg_negative_gap_forward_return: float | None = None
    notes: str | None = None


class BacktestSummary(BaseModel):
    horizon_days: int
    sample_size: int
    information_coefficient: float | None = None
    pearson_correlation: float | None = None
    avg_forward_return: float | None = None
    positive_gap_count: int
    negative_gap_count: int
    avg_positive_gap_forward_return: float | None = None
    avg_negative_gap_forward_return: float | None = None
    notes: str | None = None