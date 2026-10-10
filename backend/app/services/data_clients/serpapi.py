import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.data_clients.base import BaseAPIClient
from app.services.data_clients.quota import increment_quota


class SerpAPIClient(BaseAPIClient):
    def __init__(
        self,
        session: AsyncSession,
        transport: httpx.BaseTransport | None = None,
        max_attempts: int = 3,
        wait_min: float = 2.0,
        wait_max: float = 10.0,
    ):
        super().__init__(
            base_url="https://serpapi.com",
            transport=transport,
            max_attempts=max_attempts,
            wait_min=wait_min,
            wait_max=wait_max,
        )

        self.api_key = settings.SERPAPI_KEY
        self.session = session
        self.api_name = "serpapi"

    async def get_news_data(self, ticker: str) -> dict:
        params = {
            "engine": "google_news",
            "q": ticker,
            "api_key": self.api_key,
            "hl": "en",
            "gl": "us",
        }

        data = await self.get("/search.json", params=params)

        # Every paid call is counted in the quota table.
        await increment_quota(self.session, self.api_name)

        news_results = data.get("news_results", [])

        articles = []

        for result in news_results:
            articles.append(
                {
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "link": result.get("link", ""),
                }
            )

        return {
            "news_volume": len(news_results),
            "articles": articles,
        }