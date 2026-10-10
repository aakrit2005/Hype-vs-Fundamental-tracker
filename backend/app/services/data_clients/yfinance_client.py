import asyncio

import yfinance as yf
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.data_clients.quota import increment_quota


class YFinanceClient:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.api_name = "yfinance"

    async def get_profile(self, ticker: str) -> dict:
        # Returns basic identity data for a ticker.
        loop = asyncio.get_running_loop()

        info = await loop.run_in_executor(
            None,
            lambda: yf.Ticker(ticker).info,
        )

        await increment_quota(self.session, self.api_name)

        return {
            "name": info.get("shortName") or info.get("longName"),
            "sector": info.get("sector"),
        }

    async def get_fundamentals(self, ticker: str) -> dict:
        # Returns the fundamental fields used by the scoring engine.
        loop = asyncio.get_running_loop()

        info = await loop.run_in_executor(
            None,
            lambda: yf.Ticker(ticker).info,
        )

        await increment_quota(self.session, self.api_name)

        pe_ratio = info.get("forwardPE") or info.get("trailingPE")
        eps_growth = info.get("earningsQuarterlyGrowth")

        try:
            pe_ratio = float(pe_ratio) if pe_ratio is not None else None

        except ValueError:
            pe_ratio = None

        try:
            eps_growth = float(eps_growth) if eps_growth is not None else None

        except ValueError:
            eps_growth = None

        return {
            "pe_ratio": pe_ratio,
            "eps_growth": eps_growth,
        }