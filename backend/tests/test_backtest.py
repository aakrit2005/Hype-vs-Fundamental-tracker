from datetime import date

from sqlalchemy import select

from app.models.backtest_result import BacktestResult
from app.models.price_bar import PriceBar
from app.models.score import Score
from app.models.ticker import Ticker
from app.services.backtest.signal import (
    average,
    collect_forward_pairs,
    pearson_correlation,
    run_backtest,
    spearman_correlation,
)


def test_pearson_positive():
    value = pearson_correlation([1.0, 2.0, 3.0], [2.0, 4.0, 6.0])
    assert abs(value - 1.0) < 1e-9


def test_pearson_negative():
    value = pearson_correlation([1.0, 2.0, 3.0], [6.0, 4.0, 2.0])
    assert abs(value + 1.0) < 1e-9


def test_spearman_monotonic_nonlinear():
    # Rank correlation ignores the size of the jumps.
    value = spearman_correlation([1.0, 2.0, 3.0], [1.0, 8.0, 27.0])
    assert abs(value - 1.0) < 1e-9


def test_average_empty():
    assert average([]) is None


def test_collect_forward_pairs():
    price_dates = [
        date(2024, 1, 1),
        date(2024, 1, 2),
        date(2024, 1, 3),
        date(2024, 1, 4),
        date(2024, 1, 5),
        date(2024, 1, 6),
    ]

    close_prices = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]

    price_data = {1: (price_dates, close_prices)}

    score = Score(
        ticker_id=1,
        date=date(2024, 1, 2),
        divergence_gap=5.0,
        confidence_flag=1.0,
    )

    gaps, forward_returns, positive, negative = collect_forward_pairs(
        [score],
        price_data,
        horizon_days=2,
    )

    assert gaps == [5.0]

    # Entry 101.0, exit 103.0.
    expected = (103.0 / 101.0) - 1.0
    assert abs(forward_returns[0] - expected) < 1e-9
    assert positive == [forward_returns[0]]
    assert negative == []


async def test_run_backtest_saves_result(session):
    ticker = Ticker(symbol="CCC", name="Gamma", sector="Technology")
    session.add(ticker)
    await session.commit()

    price_dates = [date(2024, 1, 1), date(2024, 1, 2), date(2024, 1, 3)]
    close_prices = [100.0, 110.0, 121.0]

    for bar_date, close_price in zip(price_dates, close_prices):
        session.add(
            PriceBar(
                ticker_id=ticker.id,
                date=bar_date,
                close_price=close_price,
            )
        )

    session.add(
        Score(
            ticker_id=ticker.id,
            date=date(2024, 1, 1),
            hype_score=80.0,
            fund_score=30.0,
            divergence_gap=50.0,
            confidence_flag=1.0,
        )
    )

    await session.commit()

    result = await run_backtest(session, horizon_days=1)

    assert result.sample_size == 1
    assert "small" in result.notes

    saved = await session.execute(select(BacktestResult))
    assert len(saved.scalars().all()) == 1