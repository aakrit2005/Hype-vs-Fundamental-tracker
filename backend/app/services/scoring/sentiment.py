from app.core.config import settings


POSITIVE_WORDS = {
    "surge",
    "beat",
    "growth",
    "bullish",
    "upgrade",
    "record",
    "profit",
    "up",
    "gain",
    "buy",
}

NEGATIVE_WORDS = {
    "drop",
    "miss",
    "bearish",
    "downgrade",
    "loss",
    "down",
    "fall",
    "sell",
    "warn",
    "cut",
}


class SentimentAnalyzer:
    name = "base"

    def score(self, text: str) -> float:
        raise NotImplementedError


class LexiconSentimentAnalyzer(SentimentAnalyzer):
    name = "lexicon"

    def score(self, text: str) -> float:
        # Fast, dependency-free baseline using financial word lists.
        words = set(text.lower().split())

        pos_count = len(words.intersection(POSITIVE_WORDS))
        neg_count = len(words.intersection(NEGATIVE_WORDS))

        total = pos_count + neg_count

        if total == 0:
            return 0.0

        return (pos_count - neg_count) / total


class FinBertSentimentAnalyzer(SentimentAnalyzer):
    name = "finbert"

    def __init__(self):
        try:
            from transformers import pipeline

        except ImportError as exc:
            raise RuntimeError(
                "FinBERT requires the ml extra: pip install -e \".[ml]\""
            ) from exc

        # ProsusAI/finbert is pretrained on financial headlines.
        self._pipeline = pipeline(
            "text-classification",
            model="ProsusAI/finbert",
        )

    def score(self, text: str) -> float:
        if not text.strip():
            return 0.0

        result = self._pipeline(text[:512])[0]

        label = result["label"]
        confidence = float(result["confidence"])

        if label == "neutral":
            return 0.0

        sign = 1.0 if label == "positive" else -1.0

        return sign * confidence


_ANALYZER_CACHE = {}


def get_sentiment_analyzer() -> SentimentAnalyzer:
    # The model is loaded once and reused.
    key = settings.SENTIMENT_MODEL

    if key not in _ANALYZER_CACHE:
        if key == "finbert":
            _ANALYZER_CACHE[key] = FinBertSentimentAnalyzer()
        else:
            _ANALYZER_CACHE[key] = LexiconSentimentAnalyzer()

    return _ANALYZER_CACHE[key]