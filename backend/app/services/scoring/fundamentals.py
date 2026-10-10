from typing import Any

from app.services.scoring.normalizer import (
    clamp,
    invert,
    median,
    scale_optional_values,
)

# Fundamental score weighting:
# 50% comes from sector-relative P/E.
# 50% comes from EPS growth.
FUND_PE_WEIGHT = 0.5
FUND_EPS_WEIGHT = 0.5

# This cap stops one extreme P/E from controlling the whole score.
MAX_RELATIVE_PE = 3.0


def calculate_fundamental_scores(records: list[dict[str, Any]]) -> None:
    sector_pe_values = {}
    all_positive_pe_values = []

    # Collect positive P/E values by sector.
    # Negative P/E usually means the company is not profitable.
    for record in records:
        pe_ratio = record["pe_ratio"]

        if pe_ratio is not None and pe_ratio > 0:
            sector = record["sector"] or "Unknown"

            if sector not in sector_pe_values:
                sector_pe_values[sector] = []

            sector_pe_values[sector].append(pe_ratio)
            all_positive_pe_values.append(pe_ratio)

    universe_pe_median = median(all_positive_pe_values)

    relative_pe_values = []

    for record in records:
        sector = record["sector"] or "Unknown"
        sector_pe_list = sector_pe_values.get(sector, [])
        sector_peer_count = len(sector_pe_list)
        pe_median = median(sector_pe_list)

        # If the sector has too few peers, fall back to the full ticker universe.
        # The confidence flag is reduced later when this happens.
        if sector_peer_count < 2:
            pe_median = universe_pe_median

        record["_sector_peer_count"] = sector_peer_count

        pe_ratio = record["pe_ratio"]

        if pe_ratio is None:
            relative_pe = None

        elif pe_ratio <= 0:
            # Negative or zero P/E is treated as weak fundamental quality.
            relative_pe = MAX_RELATIVE_PE

        elif pe_median is None or pe_median <= 0:
            relative_pe = None

        else:
            # Relative P/E compares the ticker to its peer group.
            # A value below 1 means the ticker is cheaper than the peer median.
            # A value above 1 means the ticker is more expensive than the peer median.
            relative_pe = pe_ratio / pe_median
            relative_pe = clamp(relative_pe, 0.0, MAX_RELATIVE_PE)

        relative_pe_values.append(relative_pe)

    # Lower relative P/E should produce a higher fundamental score.
    pe_scores_raw = scale_optional_values(relative_pe_values, default=0.5)
    pe_scores = invert(pe_scores_raw)

    eps_values = []

    for record in records:
        eps_values.append(record["eps_growth"])

    # Higher EPS growth should produce a higher fundamental score.
    eps_scores = scale_optional_values(eps_values, default=0.5)

    for index, record in enumerate(records):
        pe_missing = record["pe_ratio"] is None
        eps_missing = record["eps_growth"] is None

        if pe_missing and eps_missing:
            # Neutral score when no fundamental data exists.
            fund_score = 50.0

        elif pe_missing:
            # Use EPS growth alone if P/E is missing.
            fund_score = 100.0 * eps_scores[index]

        elif eps_missing:
            # Use P/E alone if EPS growth is missing.
            fund_score = 100.0 * pe_scores[index]

        else:
            fund_score = 100.0 * (
                FUND_PE_WEIGHT * pe_scores[index]
                + FUND_EPS_WEIGHT * eps_scores[index]
            )

        record["fund_score"] = round(fund_score, 4)