from typing import Any

from app.services.scoring.normalizer import normalize_sentiment, scale_optional_values

# Hype score weighting:
# 70% comes from attention volume.
# 30% comes from sentiment.
HYPE_VOLUME_WEIGHT = 0.7
HYPE_SENTIMENT_WEIGHT = 0.3


def calculate_hype_scores(records: list[dict[str, Any]]) -> None:
    # Each record represents one ticker's raw signal for one day.
    volumes = []

    for record in records:
        volumes.append(record["volume"])

    # Volume is scaled across all tickers for the same day.
    volume_scores = scale_optional_values(volumes, default=0.5)

    for index, record in enumerate(records):
        sentiment_score = normalize_sentiment(record["sentiment"])

        hype_raw = (
            HYPE_VOLUME_WEIGHT * volume_scores[index]
            + HYPE_SENTIMENT_WEIGHT * sentiment_score
        )

        # Score is stored from 0 to 100 for readability.
        record["hype_score"] = round(100.0 * hype_raw, 4)