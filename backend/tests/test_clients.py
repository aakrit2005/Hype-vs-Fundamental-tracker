from datetime import date

import httpx
import yfinance as yf
from sqlalchemy import select

from app.models.news_article import NewsArticle
from app.models.quota_usage import QuotaUsage
from app.models.raw_signal import RawSignal
from app.models.ticker import Ticker
from app.services.data_clients.serpapi import SerpAPIClient
from app.services.data_clients.yfinance_client import YFinanceClient
from app.services.ingestion import ingest_ticker_signals


NEWS_PAYLOAD = {
    "news_results": [
        {
            "title": "Apple surge",
            "snippet": "beat expectations record profit upgrade",
            "link": "https://example.com/1",
        },
        {
            "title": "Analysts upgrade",
            "snippet": "growth and gain",
            "link": "https://example.com/2",
        },
    ]
}


def make_success_handler():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=NEWS_PAYLOAD)

    return handler


def make_flaky_handler():
    state = {"calls": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        state["calls"] += 1

        if state["calls"] == 1:
            return httpx.Response(500, json={"error": "boom"})

        return httpx.Response(200, json=NEWS_PAYLOAD)

    return handler, state


def make_failure_handler():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    return handler


async def test_serpapi_returns_articles_and_quota(session):
    transport = httpx.MockTransport(make_success_handler())

    client = SerpAPIClient(
        session,
        transport=transport,
        max_attempts=2,
        wait_min=0.01,
        wait_max=0.02,
    )

    data = await client.get_news_data("AAPL")
    await client.close()

    assert data["news_volume"] == 2
    assert len(data["articles"]) == 2
    assert data["articles"][0]["link"] == "https://example.com/1"

    result = await session.execute(
        select(QuotaUsage).where(
            QuotaUsage.api_name == "serpapi",
            QuotaUsage.date == date.today(),
        )
    )

    quota = result.scalar_one()
    assert quota.calls_made == 1


async def test_serpapi_retries_then_succeeds(session):
    handler, state = make_flaky_handler()
    transport = httpx.MockTransport(handler)

    client = SerpAPIClient(
        session,
        transport=transport,
        max_attempts=2,
        wait_min=0.01,
        wait_max=0.02,
    )

    data = await client.get_news_data("AAPL")
    await client.close()

    assert state["calls"] == 2
    assert data["news_volume"] == 2


async def test_serpapi_gives_up_after_max_attempts(session):
    transport = httpx.MockTransport(make_failure_handler())

    client = SerpAPIClient(
        session,
        transport=transport,
        max_attempts=2,
        wait_min=0.01,
        wait_max=0.02,
    )

    try:
        await client.get_news_data("AAPL")
        raise AssertionError("Expected HTTPStatusError")

    except httpx.HTTPStatusError:
        pass

    finally:
        await client.close()


class FakeTicker:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.info = {
            "forwardPE": 25.5,
            "earningsQuarterlyGrowth": 0.12,
            "shortName": "Fake Corp",
            "sector": "Technology",
        }


async def test_yfinance_fundamentals(session, monkeypatch):
    monkeypatch.setattr(yf, "Ticker", FakeTicker)

    client = YFinanceClient(session)

    data = await client.get_fundamentals("AAPL")

    assert data["pe_ratio"] == 25.5
    assert data["eps_growth"] == 0.12

    result = await session.execute(
        select(QuotaUsage).where(
            QuotaUsage.api_name == "yfinance",
            QuotaUsage.date == date.today(),
        )
    )

    quota = result.scalar_one()
    assert quota.calls_made == 1


async def test_ingestion_stores_articles_and_sentiment(session):
    session.add(Ticker(symbol="AAA", name="Alpha", sector="Technology"))
    await session.commit()

    result = await session.execute(select(Ticker))
    ticker = result.scalar_one()

    transport = httpx.MockTransport(make_success_handler())

    import app.services.ingestion as ingestion_module

    original_client = ingestion_module.SerpAPIClient

    def fake_client(session_arg):
        return original_client(
            session_arg,
            transport=transport,
            max_attempts=2,
            wait_min=0.01,
            wait_max=0.02,
        )

    ingestion_module.SerpAPIClient = fake_client

    try:
        await ingest_ticker_signals("AAA", session)

    finally:
        ingestion_module.SerpAPIClient = original_client

    result = await session.execute(
        select(RawSignal).where(RawSignal.ticker_id == ticker.id)
    )

    raw_signal = result.scalar_one()

    # Both stored snippets are fully positive under the lexicon analyzer.
    assert raw_signal.news_sentiment == 1.0
    assert raw_signal.news_volume == 2

    result = await session.execute(
        select(NewsArticle).where(NewsArticle.ticker_id == ticker.id)
    )

    assert len(result.scalars().all()) == 2