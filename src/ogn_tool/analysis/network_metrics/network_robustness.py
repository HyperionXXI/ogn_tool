from __future__ import annotations

import pandas as pd


def compute_station_removal_impact(network_metrics: dict | None) -> pd.DataFrame:
    """Simulate station removal impact from the visibility matrix.

    The computation is intentionally lightweight and operates on the existing
    aircraft/station visibility matrix produced by the visibility facade.
    """
    network_metrics = network_metrics or {}
    visibility = network_metrics.get("visibility") or {}
    matrix = visibility.get("matrix") if isinstance(visibility, dict) else None

    if not isinstance(matrix, pd.DataFrame) or matrix.empty or not {"src", "igate", "packets"}.issubset(matrix.columns):
        return pd.DataFrame(columns=[
            "station_id",
            "aircraft_lost",
            "redundancy_lost",
            "coverage_loss_ratio",
            "impact_score",
        ])

    aircraft_station_counts = matrix.groupby("src")["igate"].nunique()
    total_aircraft = int(aircraft_station_counts.shape[0])

    rows: list[dict] = []
    for station_id in sorted(matrix["igate"].dropna().astype(str).unique()):
        station_rows = matrix[matrix["igate"].astype(str) == station_id]
        impacted_aircraft = station_rows["src"].astype(str).unique().tolist()
        aircraft_lost = int(sum(1 for aircraft_id in impacted_aircraft if aircraft_station_counts.get(aircraft_id, 0) <= 1))
        redundancy_lost = int(sum(max(int(aircraft_station_counts.get(aircraft_id, 0) or 0) - 1, 0) for aircraft_id in impacted_aircraft))
        coverage_loss_ratio = float(aircraft_lost / total_aircraft) if total_aircraft else 0.0
        impact_score = float(aircraft_lost + (0.25 * redundancy_lost) + (coverage_loss_ratio * 10.0))
        rows.append({
            "station_id": station_id,
            "aircraft_lost": aircraft_lost,
            "redundancy_lost": redundancy_lost,
            "coverage_loss_ratio": coverage_loss_ratio,
            "impact_score": impact_score,
        })

    if not rows:
        return pd.DataFrame(columns=[
            "station_id",
            "aircraft_lost",
            "redundancy_lost",
            "coverage_loss_ratio",
            "impact_score",
        ])

    return pd.DataFrame(rows).sort_values("impact_score", ascending=False).reset_index(drop=True)
