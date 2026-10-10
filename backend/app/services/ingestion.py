from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.news_article import NewsArticle
from app.models.raw_signal import RawSignal
from app.models.ticker import Ticker
from app.services.data_clients.serpapi import SerpAPIClient
from app.services.data_clients.yfinance_client import YFinanceClient
from app.services.scoring.sentiment import get_sentiment_analyzer


async def ensure_ticker_exists(session: AsyncSession, symbol: str) -> Ticker:
    symbol = symbol.upper().strip()

    stmt = select(Ticker).where(Ticker.symbol == symbol)
    result = await session.execute(stmt)
    ticker = result.scalar_one_or_none()

    if ticker is not None:
        return ticker

    yfinance_client = YFinanceClient(session)

    name = symbol
    sector = None

    try:
        profile = await yfinance_client.get_profile(symbol)

        if profile.get("name"):
            name = profile["name"]

        if profile.get("sector"):
            sector = profile["sector"]

    except Exception:
        # The ticker can still be created with minimal data.
        pass

    ticker = Ticker(
        symbol=symbol,
        name=name,
        sector=sector,
        is_active=True,
    )

    session.add(ticker)
    await session.commit()

    return ticker


async def ingest_ticker_signals(ticker_symbol: str, session: AsyncSession):
    ticker_symbol = ticker_symbol.upper().strip()

    ticker = await ensure_ticker_exists(session, ticker_symbol)

    today = date.today()

    # Skip the whole day if raw data already exists.
    stmt = select(RawSignal).where(
        RawSignal.ticker_id == ticker.id,
        RawSignal.date == today,
    )

    result = await session.execute(stmt)
    existing_signal = result.scalar_one_or_none()

    if existing_signal is not None:
        print(f"Signal for {ticker_symbol} on {today} already exists. Skipping.")
        return existing_signal

    serpapi = SerpAPIClient(session)
    yfinance = YFinanceClient(session)

    try:
        hype_data = await serpapi.get_news_data(ticker_symbol)
        fund_data = await yfinance.get_fundamentals(ticker_symbol)

    finally:
        await serpapi.close()

    analyzer = get_sentiment_analyzer()
    articles = hype_data.get("articles", [])

    stmt = select(NewsArticle.url).where(
        NewsArticle.ticker_id == ticker.id,
        NewsArticle.date == today,
    )

    result = await session.execute(stmt)
    existing_urls = set(result.scalars().all())

    article_scores = []

    for article in articles:
        text = f"{article['title']} {article['snippet']}".strip()

        score_value = analyzer.score(text) if text else 0.0
        article_scores.append(score_value)

        url = (article.get("link") or None)
        url = url[:500] if url else None

        if url is not None and url in existing_urls:
            continue

        session.add(
            NewsArticle(
                ticker_id=ticker.id,
                date=today,
                title=(article.get("title") or None)[:500] if article.get("title") else None,
                snippet=(article.get("snippet") or None)[:2000] if article.get("snippet") else None,
                url=url,
                sentiment_score=score_value,
            )
        )

    # Aggregate article sentiment into one daily value.
    news_sentiment = None

    if article_scores:
        news_sentiment = sum(article_scores) / len(article_scores)

    new_signal = RawSignal(
        ticker_id=ticker.id,
        date=today,
        trends_volume=hype_data.get("news_volume"),
        news_volume=hype_data.get("news_volume"),
        news_sentiment=news_sentiment,
        pe_ratio=fund_data.get("pe_ratio"),
        eps_growth=fund_data.get("eps_growth"),
    )

    session.add(new_signal)
    await session.commit()

    print(f"Successfully ingested raw signals for {ticker_symbol}.")
    return new_signal