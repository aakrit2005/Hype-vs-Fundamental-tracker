import { apiFetch } from "./client";
import type { BacktestSummary, Score, Ticker } from "../types";

export function getTickers() {
  return apiFetch<Ticker[]>("/tickers");
}

export function getTicker(id: number) {
  return apiFetch<Ticker>(`/tickers/${id}`);
}

export function getTickerHistory(id: number, days = 90) {
  return apiFetch<Score[]>(`/tickers/${id}/history?days=${days}`);
}

export function getTickerBacktest(id: number, horizon = 5) {
  return apiFetch<BacktestSummary>(`/tickers/${id}/backtest?horizon=${horizon}`);
}