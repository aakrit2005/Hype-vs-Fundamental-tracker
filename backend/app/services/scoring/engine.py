from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.raw_signal import RawSignal
from app.models.score import Score
from app.models.ticker import Ticker
from app.services.scoring.fundamentals import calculate_fundamental_scores
from app.services.scoring.hype import calculate_hype_scores
from app.services.scoring.normalizer import clamp

# Phase 2 scoring method:
# 1. Raw hype inputs are news volume and news sentiment.
# 2. Raw fundamental inputs are P/E and EPS growth.
# 3. Volume and EPS growth are min-max scaled across tickers for the same day.
# 4. P/E is made sector-relative before scaling.
# 5. Lower relative P/E and higher EPS growth increase the fundamental score.
# 6. Divergence gap equals hype score minus fundamental score.
# 7. Confidence flag lowers when data is missing, thin, or sector coverage is weak.


def get_volume(raw_signal: RawSignal) -> float | None:
    # Trends volume is preferred when available.
    # News volume is used as the current MVP attention signal.
    if raw_signal.trends_volume is not None:
        return float(raw_signal.trends_volume)

    if raw_signal.news_volume is not None:
        return float(raw_signal.news_volume)

    return None


def build_records(rows) -> list[dict[str, Any]]:
    records = []

    for raw_signal, ticker in rows:
        records.append(
            {
                "ticker_id": ticker.id,
                "symbol": ticker.symbol,
                "sector": ticker.sector,
                "volume": get_volume(raw_signal),
                "sentiment": raw_signal.news_sentiment,
                "pe_ratio": raw_signal.pe_ratio,
                "eps_growth": raw_signal.eps_growth,
            }
        )

    return records


def calculate_confidence(record: dict[str, Any], cohort_size: int) -> float:
    # Confidence starts high and is reduced when data quality is weak.
    confidence = 1.0

    volume = record["volume"]

    if volume is None or volume < 1:
        confidence -= 0.30

    elif volume < 5:
        # Low attention volume makes the hype score less reliable.
        confidence -= 0.15

    if record["sentiment"] is None:
        confidence -= 0.10

    if record["pe_ratio"] is None:
        confidence -= 0.25

    elif record["pe_ratio"] <= 0:
        # Negative P/E is usable, but it is less comparable than positive P/E.
        confidence -= 0.10

    if record["eps_growth"] is None:
        confidence -= 0.25

    sector_peer_count = record.get("_sector_peer_count", 0)

    if sector_peer_count < 2:
        # Sector-relative P/E is weaker without enough sector peers.
        confidence -= 0.15

    if cohort_size < 5:
        # Cross-sectional normalization is weaker with very few tickers.
        confidence -= 0.10

    return clamp(confidence, 0.05, 1.0)


async def save_scores(
    session: AsyncSession,
    target_date: date,
    records: list[dict[str, Any]],
) -> None:
    for record in records:
        stmt = select(Score).where(
            Score.ticker_id == record["ticker_id"],
            Score.date == target_date,
        )

        result = await session.execute(stmt)
        score = result.scalar_one_or_none()

        # Updating an existing row keeps ingestion idempotent.
        if score is None:
            score = Score(
                ticker_id=record["ticker_id"],
                date=target_date,
            )
            session.add(score)

        score.hype_score = record["hype_score"]
        score.fund_score = record["fund_score"]
        score.divergence_gap = record["divergence_gap"]
        score.confidence_flag = record["confidence_flag"]

    await session.commit()


async def calculate_scores_for_date(
    session: AsyncSession,
    target_date: date,
) -> int:
    stmt = (
        select(RawSignal, Ticker)
        .join(Ticker, RawSignal.ticker_id == Ticker.id)
        .where(RawSignal.date == target_date)
    )

    result = await session.execute(stmt)
    rows = result.all()

    if not rows:
        return 0

    records = build_records(rows)

    calculate_hype_scores(records)
    calculate_fundamental_scores(records)

    for record in records:
        record["divergence_gap"] = round(
            record["hype_score"] - record["fund_score"],
            4,
        )

        record["confidence_flag"] = round(
            calculate_confidence(record, len(records)),
            4,
        )

    await save_scores(session, target_date, records)

    return len(records)