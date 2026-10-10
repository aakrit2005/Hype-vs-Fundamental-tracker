export function formatNumber(value: number | null): string {
  if (value === null || value === undefined) {
    return "n/a";
  }

  return value.toFixed(2);
}

export function formatPercent(value: number | null): string {
  if (value === null || value === undefined) {
    return "n/a";
  }

  return `${(value * 100).toFixed(2)}%`;
}

export function formatDate(isoDate: string): string {
  // Turns 2026-10-02 into Oct 2, 2026.
  const parsed = new Date(`${isoDate}T00:00:00`);

  return parsed.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export function formatGap(value: number | null): string {
  if (value === null || value === undefined) {
    return "n/a";
  }

  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}`;
}

export function gapColor(value: number | null): string {
  // Large positive gaps are warnings, large negative gaps are opportunities.
  if (value === null || value === undefined) {
    return "var(--muted)";
  }

  if (value >= 25) {
    return "var(--red)";
  }

  if (value <= -25) {
    return "var(--blue)";
  }

  return "var(--teal)";
}

export function fundBarColor(fund: number | null, gap: number | null): string {
  // Visual bands for the fundamentals bar.
  if (fund === null || fund === undefined) {
    return "var(--muted)";
  }

  if (fund < 20) {
    return "var(--blue)";
  }

  // Mid-range fundamentals paired with extreme overhype get highlighted.
  if (fund >= 30 && fund < 40 && gap !== null && gap > 25) {
    return "var(--red)";
  }

  return "var(--teal)";
}

export function confidenceColor(value: number | null): string {
  if (value === null || value === undefined) {
    return "var(--muted)";
  }

  if (value >= 0.8) {
    return "var(--green)";
  }

  if (value >= 0.5) {
    return "var(--amber)";
  }

  return "var(--red)";
}