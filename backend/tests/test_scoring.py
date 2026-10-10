from datetime import date

from app.models.raw_signal import RawSignal
from app.models.score import Score
from app.models.ticker import Ticker
from app.services.scoring.engine import calculate_confidence, calculate_scores_for_date
from app.services.scoring.fundamentals import calculate_fundamental_scores
from app.services.scoring.hype import calculate_hype_scores
from app.services.scoring.normalizer import (
    invert,
    median,
    min_max_scale,
    normalize_sentiment,
    scale_optional_values,
)


def test_min_max_scale_basic():
    assert min_max_scale([1.0, 2.0, 3.0]) == [0.0, 0.5, 1.0]


def test_min_max_scale_equal_values():
    # Equal values must not divide by zero.
    assert min_max_scale([5.0, 5.0]) == [0.5, 0.5]


def test_scale_optional_values_missing():
    # Missing values receive a neutral score.
    assert scale_optional_values([None, 10.0, 20.0]) == [0.5, 0.0, 1.0]


def test_normalize_sentiment():
    assert normalize_sentiment(-1.0) == 0.0
    assert normalize_sentiment(0.0) == 0.5
    assert normalize_sentiment(1.0) == 1.0
    assert normalize_sentiment(None) == 0.5


def test_invert():
    assert invert([0.0, 0.25, 1.0]) == [1.0, 0.75, 0.0]


def test_median():
    assert median([3.0, 1.0, 2.0]) == 2.0
    assert median([1.0, 2.0, 3.0, 4.0]) == 2.5
    assert median([]) is None


def test_hype_scores():
    records = [
        {"volume": 10.0, "sentiment": 1.0},
        {"volume": 20.0, "sentiment": -1.0},
    ]

    calculate_hype_scores(records)

    # 100 * (0.7 * volume_norm + 0.3 * sentiment_norm)
    assert records[0]["hype_score"] == 30.0
    assert records[1]["hype_score"] == 70.0


def test_fundamental_scores_sector_relative():
    records = [
        {"sector": "Technology", "pe_ratio": 10.0, "eps_growth": None},
        {"sector": "Technology", "pe_ratio": 30.0, "eps_growth": None},
    ]

    calculate_fundamental_scores(records)

    # Sector median P/E is 20.
    # Cheaper P/E gets the higher fundamental score.
    assert records[0]["fund_score"] == 100.0
    assert records[1]["fund_score"] == 0.0
    assert records[0]["_sector_peer_count"] == 2


def test_confidence_full_data():
    record = {
        "volume": 10.0,
        "sentiment": 0.2,
        "pe_ratio": 15.0,
        "eps_growth": 0.1,
        "_sector_peer_count": 2,
    }

    assert calculate_confidence(record, cohort_size=6) == 1.0


def test_confidence_missing_data():
    record = {
        "volume": None,
        "sentiment": None,
        "pe_ratio": None,
        "eps_growth": None,
        "_sector_peer_count": 0,
    }

    # Heavy penalties clamp to the minimum confidence.
    assert calculate_confidence(record, cohort_size=1) == 0.05


async def test_calculate_scores_for_date(session):
    ticker_a = Ticker(symbol="AAA", name="Alpha", sector="Technology")
    ticker_b = Ticker(symbol="BBB", name="Beta", sector="Technology")

    session.add_all([ticker_a, ticker_b])
    await session.commit()

    today = date.today()

    session.add_all(
        [
            RawSignal(
                ticker_id=ticker_a.id,
                date=today,
                trends_volume=10.0,
                news_volume=10.0,
                news_sentiment=1.0,
                pe_ratio=10.0,
                eps_growth=None,
            ),
            RawSignal(
                ticker_id=ticker_b.id,
                date=today,
                trends_volume=20.0,
                news_volume=20.0,
                news_sentiment=-1.0,
                pe_ratio=30.0,
                eps_growth=None,
            ),
        ]
    )

    await session.commit()

    count = await calculate_scores_for_date(session, today)
    assert count == 2

    from sqlalchemy import select

    result = await session.execute(
        select(Score).where(Score.ticker_id == ticker_a.id)
    )
    score_a = result.scalar_one()

    assert score_a.hype_score == 30.0
    assert score_a.fund_score == 100.0
    assert score_a.divergence_gap == -70.0

    # Rerunning must not create duplicate score rows.
    await calculate_scores_for_date(session, today)

    result = await session.execute(select(Score))
    assert len(result.scalars().all()) == 2