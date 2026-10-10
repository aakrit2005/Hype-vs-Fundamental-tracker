export interface Ticker {
  id: number;
  symbol: string;
  name: string | null;
  sector: string | null;
  is_active: boolean;
}

export interface Score {
  id: number;
  ticker_id: number;
  date: string;
  hype_score: number | null;
  fund_score: number | null;
  divergence_gap: number | null;
  confidence_flag: number | null;
}

export interface LeaderboardScore extends Score {
  symbol: string;
}

export interface LiveLookupResponse {
  ticker: Ticker;
  score: Score;
}

export interface User {
  id: number;
  email: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface BacktestResult {
  id: number;
  run_date: string;
  horizon_days: number;
  min_confidence: number;
  sample_size: number;
  information_coefficient: number | null;
  pearson_correlation: number | null;
  avg_forward_return: number | null;
  positive_gap_count: number;
  negative_gap_count: number;
  avg_positive_gap_forward_return: number | null;
  avg_negative_gap_forward_return: number | null;
  notes: string | null;
}

export interface BacktestSummary {
  horizon_days: number;
  sample_size: number;
  information_coefficient: number | null;
  pearson_correlation: number | null;
  avg_forward_return: number | null;
  positive_gap_count: number;
  negative_gap_count: number;
  avg_positive_gap_forward_return: number | null;
  avg_negative_gap_forward_return: number | null;
  notes: string | null;
}

export interface Alert {
  id: number;
  ticker_id: number;
  symbol: string;
  date: string;
  message: string;
  is_read: boolean;
  created_at: string;
}