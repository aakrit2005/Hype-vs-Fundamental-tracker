import { useEffect, useState } from "react";

import { getBacktests } from "../api/backtest";
import { getErrorMessage } from "../api/client";
import { formatNumber, formatPercent } from "../utils";
import type { BacktestResult } from "../types";

export function BacktestResults() {
  const [results, setResults] = useState<BacktestResult[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    getBacktests()
      .then(setResults)
      .catch((error) => setError(getErrorMessage(error)));
  }, []);

  return (
    <div>
      <h1>Saved Backtest Results</h1>

      {error && <p className="error">{error}</p>}

      <table>
        <thead>
          <tr>
            <th>Run Date</th>
            <th>Horizon</th>
            <th>Sample</th>
            <th>IC</th>
            <th>Pearson</th>
            <th>Avg Forward Return</th>
            <th>Positive Gap Count</th>
            <th>Negative Gap Count</th>
            <th>Notes</th>
          </tr>
        </thead>

        <tbody>
          {results.map((result) => (
            <tr key={result.id}>
              <td>{result.run_date}</td>
              <td>{result.horizon_days} days</td>
              <td>{result.sample_size}</td>
              <td>{formatNumber(result.information_coefficient)}</td>
              <td>{formatNumber(result.pearson_correlation)}</td>
              <td>{formatPercent(result.avg_forward_return)}</td>
              <td>{result.positive_gap_count}</td>
              <td>{result.negative_gap_count}</td>
              <td>{result.notes ?? ""}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}