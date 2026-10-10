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

import type { Score } from "../types";

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend
);

interface HistoryChartProps {
  history: Score[];
}

export function HistoryChart({ history }: HistoryChartProps) {
  // The API returns history newest first.
  // The chart needs oldest first.
  const sorted = [...history].sort((a, b) => a.date.localeCompare(b.date));

  const data = {
    labels: sorted.map((item) => item.date),
    datasets: [
      {
        label: "Hype Score",
        data: sorted.map((item) => item.hype_score) as (number | null)[],
        borderColor: "#2563eb",
        backgroundColor: "#2563eb",
        tension: 0.2,
        spanGaps: true,
      },
      {
        label: "Fundamentals Score",
        data: sorted.map((item) => item.fund_score) as (number | null)[],
        borderColor: "#16a34a",
        backgroundColor: "#16a34a",
        tension: 0.2,
        spanGaps: true,
      },
    ],
  };

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: "top" as const,
      },
    },
  };

  return <Line data={data} options={options} />;
}