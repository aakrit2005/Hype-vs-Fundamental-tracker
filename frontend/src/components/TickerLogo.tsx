import { useState } from "react";

// Maps symbols to company domains so real logos can be fetched.
const LOGO_DOMAINS: Record<string, string> = {
  AAPL: "apple.com",
  TSLA: "tesla.com",
  NVDA: "nvidia.com",
  MSFT: "microsoft.com",
  AMZN: "amazon.com",
  META: "meta.com",
  AMD: "amd.com",
  JPM: "jpmorganchase.com",
  GOOG: "alphabet.com",
  GOOGL: "alphabet.com",
  NFLX: "netflix.com",
  DIS: "disney.com",
  BA: "boeing.com",
  COIN: "coinbase.com",
  PLTR: "palantir.com",
  ORCL: "oracle.com",
  INTC: "intel.com",
};

interface TickerLogoProps {
  symbol: string;
}

export function TickerLogo({ symbol }: TickerLogoProps) {
  const [failed, setFailed] = useState(false);

  const domain = LOGO_DOMAINS[symbol];

  // Unknown symbols fall back to a two-letter tile.
  if (!domain || failed) {
    return <span className="logo-tile logo-fallback">{symbol.slice(0, 2)}</span>;
  }

  return (
    <span className="logo-tile">
      <img
        src={`https://logo.clearbit.com/${domain}`}
        alt={symbol}
        onError={() => setFailed(true)}
      />
    </span>
  );
}