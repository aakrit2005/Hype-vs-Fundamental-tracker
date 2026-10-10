import httpx
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential


class BaseAPIClient:
    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
        transport: httpx.BaseTransport | None = None,
        max_attempts: int = 3,
        wait_min: float = 2.0,
        wait_max: float = 10.0,
    ):
        # Transport injection lets tests replace the network with mock responses.
        self.client = httpx.AsyncClient(
            base_url=base_url,
            timeout=timeout,
            transport=transport,
        )

        self.max_attempts = max_attempts
        self.wait_min = wait_min
        self.wait_max = wait_max

    async def get(self, endpoint: str, params: dict | None = None) -> dict:
        result = None

        # Retries transient failures with exponential backoff.
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(self.max_attempts),
            wait=wait_exponential(
                multiplier=1,
                min=self.wait_min,
                max=self.wait_max,
            ),
            reraise=True,
        ):
            with attempt:
                response = await self.client.get(endpoint, params=params)

                # Raises automatically for 4xx and 5xx responses.
                response.raise_for_status()

                result = response.json()

        return result

    async def close(self):
        # Closes the connection pool to prevent memory leaks.
        await self.client.aclose()