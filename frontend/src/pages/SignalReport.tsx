import { useEffect, useMemo, useState } from "react";

import {
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js";
import { Line } from "react-chartjs-2";

import { getBacktests } from "../api/backtest";
import { getErrorMessage } from "../api/client";
import { formatNumber, formatPercent } from "../utils";
import type { BacktestResult } from "../types";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend
);

export function SignalReport() {
  const [results, setResults] = useState<BacktestResult[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    getBacktests(200)
      .then(setResults)
      .catch((error) => setError(getErrorMessage(error)));
  }, []);

  const horizons = useMemo(
    () =>
      Array.from(new Set(results.map((item) => item.horizon_days))).sort(
        (a, b) => a - b
      ),
    [results]
  );

  const dates = useMemo(
    () => Array.from(new Set(results.map((item) => item.run_date))).sort(),
    [results]
  );

  const datasets = horizons.map((horizon) => ({
    label: `${horizon}-day IC`,
    data: dates.map((day) => {
      const match = results.find(
        (item) => item.run_date === day && item.horizon_days === horizon
      );

      return match ? match.information_coefficient : null;
    }) as (number | null)[],
    spanGaps: true,
  }));

  // The API returns newest first, so the first row per horizon is the latest.
  const latestByHorizon = horizons.map((horizon) =>
    results.find((item) => item.horizon_days === horizon)
  );

  return (
    <div>
      <h1>Signal Report</h1>

      {error && <p className="error">{error}</p>}

      <div className="card">
        <h2>Methodology</h2>

        <ul>
          <li>
            Hype score combines cross-sectional news volume (70%) and headline
            sentiment (30%), min-max normalized across the tracked universe
            each day.
          </li>
          <li>
            Fundamentals score combines sector-relative P/E (50%) and EPS
            growth (50%), min-max normalized each day.
          </li>
          <li>
            The signal is the divergence gap: hype score minus fundamentals
            score.
          </li>
          <li>
            Validation uses the information coefficient: rank correlation
            between the divergence gap on a score date and the realized
            forward return over the horizon, measured in trading days.
          </li>
          <li>
            Scores with a confidence flag below 0.5 are excluded from
            alerting, and small samples are labelled in the notes column.
          </li>
        </ul>

        <p>
          Interpretation: for a daily cross-sectional signal, an IC near 0
          means no measurable edge, around 0.03 to 0.05 is weak but
          interesting, and above 0.05 sustained over a large sample is a real
          result worth publishing.
        </p>
      </div>

      {latestByHorizon.map(
        (latest) =>
          latest && (
            <div className="card" key={latest.horizon_days}>
              <h2>{latest.horizon_days}-Trading-Day Horizon</h2>

              <p>Latest run: {latest.run_date}</p>
              <p>Sample size: {latest.sample_size}</p>
              <p>
                Information coefficient:{" "}
                {formatNumber(latest.information_coefficient)}
              </p>
              <p>
                Average forward return:{" "}
                {formatPercent(latest.avg_forward_return)}
              </p>

              {latest.notes && <p>{latest.notes}</p>}
            </div>
          )
      )}

      <div className="card">
        <h2>Information Coefficient Over Time</h2>

        {results.length === 0 ? (
          <p>No backtest runs recorded yet.</p>
        ) : (
          <Line
            data={{ labels: dates, datasets }}
            options={{
              responsive: true,
              plugins: { legend: { position: "top" as const } },
            }}
          />
        )}
      </div>

      <p className="footer-note">
        This report is published for research transparency. It is not
        investment advice. Past correlation does not guarantee future
        returns, and transaction costs are not modeled.
      </p>
    </div>
  );
}