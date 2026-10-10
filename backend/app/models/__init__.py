from app.models.ticker import Ticker
from app.models.raw_signal import RawSignal
from app.models.score import Score
from app.models.quota_usage import QuotaUsage
from app.models.price_bar import PriceBar
from app.models.backtest_result import BacktestResult
from app.models.user import User
from app.models.watchlist import Watchlist
from app.models.news_article import NewsArticle
from app.models.alert import Alert


# Importing these models lets SQLAlchemy see all tables.
__all__ = [
    "Ticker",
    "RawSignal",
    "Score",
    "QuotaUsage",
    "PriceBar",
    "BacktestResult",
    "User",
    "Watchlist",
    "NewsArticle",
    "Alert",
]