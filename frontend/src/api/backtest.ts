import { apiFetch } from "./client";
import type { BacktestResult } from "../types";

export function getBacktests(limit = 20) {
  return apiFetch<BacktestResult[]>(`/backtest/summary?limit=${limit}`);
}