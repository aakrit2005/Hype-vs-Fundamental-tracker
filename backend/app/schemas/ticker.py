
from pydantic import BaseModel, ConfigDict


class TickerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    name: str | None = None
    sector: str | None = None
    is_active: bool