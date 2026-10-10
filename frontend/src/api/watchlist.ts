import { apiFetch } from "./client";
import type { Ticker } from "../types";

export function getWatchlist() {
  return apiFetch<Ticker[]>("/watchlist");
}

export function addToWatchlist(tickerId: number) {
  return apiFetch<Ticker>("/watchlist", {
    method: "POST",
    body: JSON.stringify({
      ticker_id: tickerId,
    }),
  });
}

export function removeFromWatchlist(tickerId: number) {
  return apiFetch<void>(`/watchlist/${tickerId}`, {
    method: "DELETE",
  });
}