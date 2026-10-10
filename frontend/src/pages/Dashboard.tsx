import { useEffect, useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { getErrorMessage, getToken } from "../api/client";
import { getLeaderboard, liveLookup } from "../api/signals";
import { getTickers } from "../api/tickers";
import {
  addToWatchlist,
  getWatchlist,
  removeFromWatchlist,
} from "../api/watchlist";
import { TickerLogo } from "../components/TickerLogo";
import {
  confidenceColor,
  formatDate,
  formatGap,
  formatNumber,
  fundBarColor,
  gapColor,
} from "../utils";
import type { LeaderboardScore, Ticker } from "../types";

type SortKey =
  | "symbol"
  | "hype_score"
  | "fund_score"
  | "divergence_gap"
  | "confidence_flag";

type SignalFilter = "all" | "over" | "under";

function sortValue(row: LeaderboardScore, key: SortKey): number | string {
  if (key === "symbol") {
    return row.symbol;
  }

  if (key === "hype_score") {
    return row.hype_score ?? 0;
  }

  if (key === "fund_score") {
    return row.fund_score ?? 0;
  }

  if (key === "confidence_flag") {
    return row.confidence_flag ?? 0;
  }

  // Default ranking uses the size of the divergence gap.
  return Math.abs(row.divergence_gap ?? 0);
}

function StarIcon({ filled }: { filled: boolean }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill={filled ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
  );
}

function ArrowIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="5" y1="12" x2="19" y2="12" />
      <polyline points="12 5 19 12 12 19" />
    </svg>
  );
}

export function Dashboard() {
  const token = getToken();
  const navigate = useNavigate();

  const [rows, setRows] = useState<LeaderboardScore[]>([]);
  const [names, setNames] = useState<Record<number, string>>({});
  const [watchlistIds, setWatchlistIds] = useState<number[]>([]);

  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [liveError, setLiveError] = useState("");
  const [loadingLive, setLoadingLive] = useState(false);

  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<SignalFilter>("all");
  const [sortKey, setSortKey] = useState<SortKey>("divergence_gap");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");

  useEffect(() => {
    getLeaderboard()
      .then(setRows)
      .catch((error) => setError(getErrorMessage(error)));

    getTickers()
      .then((tickers) => {
        const map: Record<number, string> = {};

        for (const ticker of tickers) {
          map[ticker.id] = ticker.name ?? ticker.symbol;
        }

        setNames(map);
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!token) {
      return;
    }

    getWatchlist()
      .then((items) => setWatchlistIds(items.map((item) => item.id)))
      .catch(() => undefined);
  }, [token]);

  const visible = useMemo(() => {
    let list = [...rows];

    if (filter === "over") {
      list = list.filter((row) => (row.divergence_gap ?? 0) > 0);
    }

    if (filter === "under") {
      list = list.filter((row) => (row.divergence_gap ?? 0) < 0);
    }

    const query = search.trim().toLowerCase();

    if (query) {
      list = list.filter((row) => row.symbol.toLowerCase().includes(query));
    }

    list.sort((a, b) => {
      const aValue = sortValue(a, sortKey);
      const bValue = sortValue(b, sortKey);

      let result = 0;

      if (typeof aValue === "string" && typeof bValue === "string") {
        result = aValue.localeCompare(bValue);
      } else {
        result = (aValue as number) - (bValue as number);
      }

      return sortDirection === "asc" ? result : -result;
    });

    return list;
  }, [rows, filter, search, sortKey, sortDirection]);

  const stats = useMemo(() => {
    if (rows.length === 0) {
      return null;
    }

    let largest = rows[0];

    for (const row of rows) {
      if (
        Math.abs(row.divergence_gap ?? 0) >
        Math.abs(largest.divergence_gap ?? 0)
      ) {
        largest = row;
      }
    }

    const totalConfidence = rows.reduce(
      (sum, row) => sum + (row.confidence_flag ?? 0),
      0
    );

    const dates = rows.map((row) => row.date).sort();

    return {
      count: rows.length,
      largest,
      averageConfidence: totalConfidence / rows.length,
      updated: dates[dates.length - 1],
    };
  }, [rows]);

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortKey(key);
      setSortDirection("desc");
    }
  }

  async function refreshAll() {
    const [updatedRows, watchlist] = await Promise.all([
      getLeaderboard(),
      token ? getWatchlist() : Promise.resolve([] as Ticker[]),
    ]);

    setRows(updatedRows);
    setWatchlistIds(watchlist.map((item) => item.id));
  }

  async function handleLiveLookup() {
    const target = search.trim();

    if (!target) {
      return;
    }

    setLoadingLive(true);
    setLiveError("");

    try {
      await liveLookup(target);
      await refreshAll();

      setSearch("");
      setNotice(`${target.toUpperCase()} refreshed.`);
    } catch (error) {
      setLiveError(getErrorMessage(error));
    } finally {
      setLoadingLive(false);
    }
  }

  async function toggleWatch(row: LeaderboardScore) {
    if (!token) {
      navigate("/login");
      return;
    }

    try {
      if (watchlistIds.includes(row.ticker_id)) {
        await removeFromWatchlist(row.ticker_id);
        setWatchlistIds((ids) => ids.filter((id) => id !== row.ticker_id));
        setNotice(`${row.symbol} removed from watchlist.`);
      } else {
        await addToWatchlist(row.ticker_id);
        setWatchlistIds((ids) => [...ids, row.ticker_id]);
        setNotice(`${row.symbol} added to watchlist.`);
      }
    } catch (error) {
      setNotice(getErrorMessage(error));
    }
  }

  function exportCsv() {
    const header = "Symbol,Hype,Fundamentals,Gap,Confidence,Date";

    const lines = visible.map((row) =>
      [
        row.symbol,
        row.hype_score ?? "",
        row.fund_score ?? "",
        row.divergence_gap ?? "",
        row.confidence_flag ?? "",
        row.date,
      ].join(",")
    );

    const blob = new Blob([`${header}\n${lines.join("\n")}`], {
      type: "text/csv",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");

    link.href = url;
    link.download = "divergence-leaderboard.csv";
    link.click();

    URL.revokeObjectURL(url);
  }

  return (
    <div>
      <div className="page-header">
        <div>
          <p className="eyebrow">Market Intelligence</p>
          <h1>Divergence Leaderboard</h1>
          <p className="subtitle">
            Market hype, measured against fundamentals.
          </p>
        </div>

        {stats && (
          <span className="pill">
            <span className="dot" style={{ background: "var(--green)" }} />
            Updated {formatDate(stats.updated)}
          </span>
        )}
      </div>

      {stats && (
        <div className="stats">
          <div className="stat">
            <span className="stat-label">Tracked symbols</span>
            <span className="stat-value">{stats.count}</span>
          </div>

          <div className="stat">
            <span className="stat-label">Largest divergence</span>
            <span className="stat-value">
              {stats.largest.symbol} {formatGap(stats.largest.divergence_gap)}
            </span>
          </div>

          <div className="stat">
            <span className="stat-label">Average confidence</span>
            <span className="stat-value">
              {Math.round(stats.averageConfidence * 100)}%
            </span>
          </div>
        </div>
      )}

      <div className="toolbar">
        <div className="search-wrap">
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>

          <input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Search symbol..."
          />
        </div>

        <button
          className="btn btn-primary"
          onClick={handleLiveLookup}
          disabled={loadingLive}
        >
          {loadingLive ? "Searching..." : "Live Lookup"}
        </button>

        <span className="spacer" />

        <select
          value={filter}
          onChange={(event) => setFilter(event.target.value as SignalFilter)}
        >
          <option value="all">All signals</option>
          <option value="over">Overhyped</option>
          <option value="under">Underhyped</option>
        </select>

        <button className="btn-icon" title="Export CSV" onClick={exportCsv}>
          <svg
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4" />
            <polyline points="10 17 15 12 10 7" />
            <line x1="15" y1="12" x2="3" y2="12" />
          </svg>
        </button>
      </div>

      {liveError && <p className="error">{liveError}</p>}
      {error && <p className="error">{error}</p>}
      {notice && <p className="notice">{notice}</p>}

      <table>
        <thead>
          <tr>
            <th className="sortable" onClick={() => handleSort("symbol")}>
              Symbol
            </th>
            <th className="sortable" onClick={() => handleSort("hype_score")}>
              Hype
            </th>
            <th className="sortable" onClick={() => handleSort("fund_score")}>
              Fundamentals
            </th>
            <th
              className="sortable"
              onClick={() => handleSort("divergence_gap")}
            >
              Gap
            </th>
            <th
              className="sortable"
              onClick={() => handleSort("confidence_flag")}
            >
              Confidence
            </th>
            <th>Date</th>
            <th style={{ textAlign: "right" }}>Actions</th>
          </tr>
        </thead>

        <tbody>
          {visible.map((row) => {
            const starred = watchlistIds.includes(row.ticker_id);

            return (
              <tr key={row.id}>
                <td>
                  <div className="symbol-cell">
                    <TickerLogo symbol={row.symbol} />

                    <span className="symbol-name">
                      <Link
                        to={`/tickers/${row.ticker_id}`}
                        className="symbol-link"
                      >
                        <strong>{row.symbol}</strong>
                      </Link>
                      <span>{names[row.ticker_id] ?? ""}</span>
                    </span>
                  </div>
                </td>

                <td>
                  <div className="score-cell">
                    <span className="score-value">
                      {formatNumber(row.hype_score)}
                    </span>

                    <span className="bar">
                      <span
                        className="bar-fill"
                        style={{
                          width: `${row.hype_score ?? 0}%`,
                          background: "var(--blue)",
                        }}
                      />
                    </span>
                  </div>
                </td>

                <td>
                  <div className="score-cell">
                    <span className="score-value">
                      {formatNumber(row.fund_score)}
                    </span>

                    <span className="bar">
                      <span
                        className="bar-fill"
                        style={{
                          width: `${row.fund_score ?? 0}%`,
                          background: fundBarColor(
                            row.fund_score,
                            row.divergence_gap
                          ),
                        }}
                      />
                    </span>
                  </div>
                </td>

                <td>
                  <span
                    className="gap-value"
                    style={{ color: gapColor(row.divergence_gap) }}
                  >
                    {formatGap(row.divergence_gap)}
                  </span>
                </td>

                <td>
                  <span className="conf-cell">
                    <span
                      className="dot"
                      style={{
                        background: confidenceColor(row.confidence_flag),
                      }}
                    />
                    {Math.round((row.confidence_flag ?? 0) * 100)}%
                  </span>
                </td>

                <td className="date-cell">{formatDate(row.date)}</td>

                <td>
                  <div className="actions-cell">
                    <button
                      className={
                        starred ? "action-btn starred" : "action-btn"
                      }
                      title="Toggle watchlist"
                      onClick={() => toggleWatch(row)}
                    >
                      <StarIcon filled={starred} />
                    </button>

                    <button
                      className="action-btn"
                      title="Open detail"
                      onClick={() => navigate(`/tickers/${row.ticker_id}`)}
                    >
                      <ArrowIcon />
                    </button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      <p className="table-footer">Showing {visible.length} symbols</p>
    </div>
  );
}