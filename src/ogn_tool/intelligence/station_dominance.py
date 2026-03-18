from __future__ import annotations

import pandas as pd

from ogn_tool.analysis.network_metrics.visibility import build_visibility_matrix

from .contracts import NetworkMetrics, ensure_metrics


OUTPUT_COLUMNS = [
    "station_id",
    "total_aircraft_count",
    "unique_aircraft_count",
    "shared_aircraft_count",
    "dominance_ratio",
    "dominance_rank",
]


def compute_station_dominance(
    observations: pd.DataFrame,
    network_metrics: NetworkMetrics | None = None,
) -> pd.DataFrame:
    """Compute how much each station contributes unique aircraft coverage."""
    _ = ensure_metrics(network_metrics)

    if not isinstance(observations, pd.DataFrame) or observations.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    matrix = build_visibility_matrix(observations)
    if not isinstance(matrix, pd.DataFrame) or matrix.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    station_counts = matrix.groupby("igate")["src"].nunique()
    aircraft_station_counts = matrix.groupby("src")["igate"].nunique()

    unique_mask = matrix["src"].map(aircraft_station_counts).eq(1)
    unique_counts = matrix.loc[unique_mask].groupby("igate")["src"].nunique()

    rows: list[dict[str, object]] = []
    for station_id in sorted(matrix["igate"].dropna().astype(str).unique().tolist()):
        total_aircraft_count = int(station_counts.get(station_id, 0) or 0)
        unique_aircraft_count = int(unique_counts.get(station_id, 0) or 0)
        shared_aircraft_count = max(total_aircraft_count - unique_aircraft_count, 0)
        dominance_ratio = (
            float(unique_aircraft_count / total_aircraft_count)
            if total_aircraft_count > 0
            else 0.0
        )

        rows.append(
            {
                "station_id": station_id,
                "total_aircraft_count": total_aircraft_count,
                "unique_aircraft_count": unique_aircraft_count,
                "shared_aircraft_count": shared_aircraft_count,
                "dominance_ratio": dominance_ratio,
            }
        )

    if not rows:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    result = pd.DataFrame(rows).sort_values(
        ["dominance_ratio", "unique_aircraft_count", "station_id"],
        ascending=[False, False, True],
    ).reset_index(drop=True)
    result["dominance_rank"] = range(1, len(result) + 1)
    return result[OUTPUT_COLUMNS]
