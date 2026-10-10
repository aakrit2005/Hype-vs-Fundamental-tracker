from app.services.scoring.sentiment import (
    LexiconSentimentAnalyzer,
    get_sentiment_analyzer,
)


def test_lexicon_positive():
    analyzer = LexiconSentimentAnalyzer()

    value = analyzer.score("stock surge after beat expectations record profit upgrade")
    assert value == 1.0


def test_lexicon_negative():
    analyzer = LexiconSentimentAnalyzer()

    value = analyzer.score("stock drop after miss and downgrade warn cut")
    assert value == -1.0


def test_lexicon_neutral():
    analyzer = LexiconSentimentAnalyzer()

    assert analyzer.score("company announces conference Tuesday") == 0.0


def test_factory_returns_lexicon_by_default():
    assert isinstance(get_sentiment_analyzer(), LexiconSentimentAnalyzer)