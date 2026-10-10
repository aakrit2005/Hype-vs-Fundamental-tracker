import { apiFetch } from "./client";
import type { LeaderboardScore, LiveLookupResponse } from "../types";

export function getLeaderboard(limit = 50) {
  return apiFetch<LeaderboardScore[]>(`/signals/leaderboard?limit=${limit}`);
}

export function liveLookup(symbol: string) {
  return apiFetch<LiveLookupResponse>("/signals/live", {
    method: "POST",
    body: JSON.stringify({
      symbol,
    }),
  });
}