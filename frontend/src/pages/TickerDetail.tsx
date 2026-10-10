import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { getErrorMessage, getToken } from "../api/client";
import {
  getTicker,
  getTickerBacktest,
  getTickerHistory,
} from "../api/tickers";
import { addToWatchlist } from "../api/watchlist";
import { HistoryChart } from "../components/HistoryChart";
import { formatNumber, formatPercent } from "../utils";
import type { BacktestSummary, Score, Ticker } from "../types";

export function TickerDetail() {
  const { id } = useParams();

  const tickerId = Number(id);
  const validId = Number.isInteger(tickerId) && tickerId > 0;

  const token = getToken();

  const [ticker, setTicker] = useState<Ticker | null>(null);
  const [history, setHistory] = useState<Score[]>([]);
  const [backtest, setBacktest] = useState<BacktestSummary | null>(null);

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!validId) {
      setError("Invalid ticker id.");
      return;
    }

    Promise.all([
      getTicker(tickerId),
      getTickerHistory(tickerId, 180),
      getTickerBacktest(tickerId, 5),
    ])
      .then(([tickerData, historyData, backtestData]) => {
        setTicker(tickerData);
        setHistory(historyData);
        setBacktest(backtestData);
      })
      .catch((error) => setError(getErrorMessage(error)));
  }, [tickerId, validId]);

  async function handleAddToWatchlist() {
    if (!ticker) {
      return;
    }

    try {
      await addToWatchlist(ticker.id);
      setMessage("Ticker added to watchlist.");
    } catch (error) {
      setMessage(getErrorMessage(error));
    }
  }

  if (!validId) {
    return <p className="error">{error}</p>;
  }

  const latestScore = history.length > 0 ? history[0] : null;

  return (
    <div>
      <p>
        <Link to="/">Back to Dashboard</Link>
      </p>

      {error && <p className="error">{error}</p>}
      {message && <p>{message}</p>}

      {ticker && (
        <div className="card">
          <h1>{ticker.symbol}</h1>

          <p>
            {ticker.name ?? "Unknown name"} | Sector: {ticker.sector ?? "Unknown"}
          </p>

          {token && <button onClick={handleAddToWatchlist}>Add to Watchlist</button>}
        </div>
      )}

      {latestScore && (
        <div className="card">
          <h2>Latest Score</h2>

          <p>
            Date: {latestScore.date}
          </p>

          <p>
            Hype: {formatNumber(latestScore.hype_score)} | Fundamentals:{" "}
            {formatNumber(latestScore.fund_score)} | Gap:{" "}
            {formatNumber(latestScore.divergence_gap)} | Confidence:{" "}
            {formatNumber(latestScore.confidence_flag)}
          </p>
        </div>
      )}

      {backtest && (
        <div className="card">
          <h2>5-Trading-Day Backtest Summary</h2>

          <p>
            Sample size: {backtest.sample_size}
          </p>

          <p>
            Information coefficient: {formatNumber(backtest.information_coefficient)}
          </p>

          <p>
            Average forward return: {formatPercent(backtest.avg_forward_return)}
          </p>

          {backtest.notes && <p>{backtest.notes}</p>}
        </div>
      )}

      <div className="card">
        <h2>Hype vs Fundamentals</h2>

        {history.length === 0 ? (
          <p>No score history yet.</p>
        ) : (
          <HistoryChart history={history} />
        )}
      </div>
    </div>
  );
}