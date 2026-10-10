from fastapi import APIRouter

from app.api.v1 import alerts, auth, backtest, signals, tickers, watchlist


api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(tickers.router)
api_router.include_router(signals.router)
api_router.include_router(backtest.router)
api_router.include_router(watchlist.router)
api_router.include_router(alerts.router)