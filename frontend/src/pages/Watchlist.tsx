import type { FormEvent } from "react";
import { useEffect, useState } from "react";
import { Navigate } from "react-router-dom";

import { getErrorMessage, getToken } from "../api/client";
import { getTickers } from "../api/tickers";
import {
  addToWatchlist,
  getWatchlist,
  removeFromWatchlist,
} from "../api/watchlist";
import type { Ticker } from "../types";

export function Watchlist() {
  const token = getToken();

  const [watchlist, setWatchlist] = useState<Ticker[]>([]);
  const [tickers, setTickers] = useState<Ticker[]>([]);
  const [selectedId, setSelectedId] = useState(0);

  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    if (!token) {
      return;
    }

    Promise.all([getWatchlist(), getTickers()])
      .then(([watchlistData, tickerData]) => {
        setWatchlist(watchlistData);
        setTickers(tickerData);
      })
      .catch((error) => setError(getErrorMessage(error)));
  }, [token]);

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  const availableTickers = tickers.filter(
    (ticker) => !watchlist.some((item) => item.id === ticker.id)
  );

  async function handleAdd(event: FormEvent) {
    event.preventDefault();

    if (!selectedId) {
      return;
    }

    try {
      await addToWatchlist(selectedId);

      const updated = await getWatchlist();
      setWatchlist(updated);

      setSelectedId(0);
      setMessage("Ticker added to watchlist.");
    } catch (error) {
      setMessage(getErrorMessage(error));
    }
  }

  async function handleRemove(ticker: Ticker) {
    try {
      await removeFromWatchlist(ticker.id);

      setWatchlist((current) =>
        current.filter((item) => item.id !== ticker.id)
      );

      setMessage(`${ticker.symbol} removed from watchlist.`);
    } catch (error) {
      setMessage(getErrorMessage(error));
    }
  }

  return (
    <div>
      <h1>Watchlist</h1>

      {error && <p className="error">{error}</p>}
      {message && <p>{message}</p>}

      <form onSubmit={handleAdd} className="row">
        <select
          value={selectedId}
          onChange={(event) => setSelectedId(Number(event.target.value))}
        >
          <option value={0}>Select a ticker</option>

          {availableTickers.map((ticker) => (
            <option key={ticker.id} value={ticker.id}>
              {ticker.symbol}
            </option>
          ))}
        </select>

        <button>Add</button>
      </form>

      <table>
        <thead>
          <tr>
            <th>Symbol</th>
            <th>Name</th>
            <th>Sector</th>
            <th>Actions</th>
          </tr>
        </thead>

        <tbody>
          {watchlist.map((ticker) => (
            <tr key={ticker.id}>
              <td>{ticker.symbol}</td>
              <td>{ticker.name ?? "Unknown"}</td>
              <td>{ticker.sector ?? "Unknown"}</td>

              <td>
                <button onClick={() => handleRemove(ticker)}>Remove</button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}