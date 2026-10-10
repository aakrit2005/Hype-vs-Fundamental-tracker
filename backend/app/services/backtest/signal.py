import math
from bisect import bisect_right
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.backtest_result import BacktestResult
from app.models.price_bar import PriceBar
from app.models.score import Score


def average(values: list[float]) -> float | None:
    # Returns the arithmetic mean.
    if not values:
        return None

    return sum(values) / len(values)


def pearson_correlation(x_values: list[float], y_values: list[float]) -> float | None:
    # Measures linear correlation between two lists.
    if len(x_values) != len(y_values):
        return None

    sample_size = len(x_values)

    if sample_size < 3:
        return None

    mean_x = sum(x_values) / sample_size
    mean_y = sum(y_values) / sample_size

    covariance = 0.0
    variance_x = 0.0
    variance_y = 0.0

    for x_value, y_value in zip(x_values, y_values):
        diff_x = x_value - mean_x
        diff_y = y_value - mean_y

        covariance += diff_x * diff_y
        variance_x += diff_x * diff_x
        variance_y += diff_y * diff_y

    if variance_x == 0.0 or variance_y == 0.0:
        return None

    return covariance / math.sqrt(variance_x * variance_y)


def rank_values(values: list[float]) -> list[float]:
    # Converts values into ranks.
    # Equal values receive the average rank.
    indexed = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)

    i = 0

    while i < len(indexed):
        j = i

        while (
            j + 1 < len(indexed)
            and values[indexed[j + 1]] == values[indexed[i]]
        ):
            j += 1

        average_rank = (i + j) / 2.0 + 1.0

        for k in range(i, j + 1):
            ranks[indexed[k]] = average_rank

        i = j + 1

    return ranks


def spearman_correlation(x_values: list[float], y_values: list[float]) -> float | None:
    # Spearman correlation measures rank correlation.
    # This is used as the information coefficient.
    if len(x_values) != len(y_values):
        return None

    if len(x_values) < 3:
        return None

    x_ranks = rank_values(x_values)
    y_ranks = rank_values(y_values)

    return pearson_correlation(x_ranks, y_ranks)


async def load_price_data(
    session: AsyncSession,
) -> dict[int, tuple[list[date], list[float]]]:
    # Loads price history grouped by ticker.
    stmt = select(PriceBar).order_by(
        PriceBar.ticker_id,
        PriceBar.date,
    )

    result = await session.execute(stmt)
    price_bars = result.scalars().all()

    price_data: dict[int, tuple[list[date], list[float]]] = {}

    for price_bar in price_bars:
        if price_bar.ticker_id not in price_data:
            price_data[price_bar.ticker_id] = ([], [])

        price_data[price_bar.ticker_id][0].append(price_bar.date)
        price_data[price_bar.ticker_id][1].append(price_bar.close_price)

    return price_data


def collect_forward_pairs(
    scores: list[Score],
    price_data: dict[int, tuple[list[date], list[float]]],
    horizon_days: int,
) -> tuple[list[float], list[float], list[float], list[float]]:
    gaps: list[float] = []
    forward_returns: list[float] = []
    positive_gap_returns: list[float] = []
    negative_gap_returns: list[float] = []

    for score in scores:
        if score.divergence_gap is None:
            continue

        ticker_price_data = price_data.get(score.ticker_id)

        if ticker_price_data is None:
            continue

        price_dates, close_prices = ticker_price_data

        if not price_dates:
            continue

        # Find the latest trading day on or before the score date.
        index = bisect_right(price_dates, score.date) - 1

        if index < 0:
            continue

        # Horizon is measured in trading days.
        forward_index = index + horizon_days

        if forward_index >= len(close_prices):
            continue

        entry_price = close_prices[index]
        exit_price = close_prices[forward_index]

        if entry_price <= 0:
            continue

        forward_return = (exit_price / entry_price) - 1.0

        gaps.append(score.divergence_gap)
        forward_returns.append(forward_return)

        if score.divergence_gap >= 0:
            positive_gap_returns.append(forward_return)
        else:
            negative_gap_returns.append(forward_return)

    return gaps, forward_returns, positive_gap_returns, negative_gap_returns


def build_metrics(
    horizon_days: int,
    gaps: list[float],
    forward_returns: list[float],
    positive_gap_returns: list[float],
    negative_gap_returns: list[float],
) -> dict:
    sample_size = len(gaps)

    information_coefficient = spearman_correlation(gaps, forward_returns)
    pearson = pearson_correlation(gaps, forward_returns)

    notes = ""

    if sample_size == 0:
        notes = "No usable score and price pairs were found."

    elif sample_size < 20:
        notes = "Sample size is small. Results are for monitoring only."

    return {
        "horizon_days": horizon_days,
        "sample_size": sample_size,
        "information_coefficient": information_coefficient,
        "pearson_correlation": pearson,
        "avg_forward_return": average(forward_returns),
        "positive_gap_count": len(positive_gap_returns),
        "negative_gap_count": len(negative_gap_returns),
        "avg_positive_gap_forward_return": average(positive_gap_returns),
        "avg_negative_gap_forward_return": average(negative_gap_returns),
        "notes": notes,
    }


async def run_backtest(
    session: AsyncSession,
    horizon_days: int,
    min_confidence: float = 0.0,
) -> BacktestResult:
    stmt = select(Score).where(
        Score.divergence_gap.is_not(None),
        Score.confidence_flag >= min_confidence,
    )

    result = await session.execute(stmt)
    scores = result.scalars().all()

    price_data = await load_price_data(session)

    gaps, forward_returns, positive_gap_returns, negative_gap_returns = (
        collect_forward_pairs(
            scores,
            price_data,
            horizon_days,
        )
    )

    metrics = build_metrics(
        horizon_days,
        gaps,
        forward_returns,
        positive_gap_returns,
        negative_gap_returns,
    )

    backtest_result = BacktestResult(
        run_date=date.today(),
        min_confidence=min_confidence,
        **metrics,
    )

    session.add(backtest_result)
    await session.commit()

    return backtest_result


async def calculate_backtest_summary_for_ticker(
    session: AsyncSession,
    ticker_id: int,
    horizon_days: int,
    min_confidence: float = 0.0,
) -> dict:
    stmt = select(Score).where(
        Score.ticker_id == ticker_id,
        Score.divergence_gap.is_not(None),
        Score.confidence_flag >= min_confidence,
    )

    result = await session.execute(stmt)
    scores = result.scalars().all()

    price_data = await load_price_data(session)

    gaps, forward_returns, positive_gap_returns, negative_gap_returns = (
        collect_forward_pairs(
            scores,
            price_data,
            horizon_days,
        )
    )

    return build_metrics(
        horizon_days,
        gaps,
        forward_returns,
        positive_gap_returns,
        negative_gap_returns,
    )