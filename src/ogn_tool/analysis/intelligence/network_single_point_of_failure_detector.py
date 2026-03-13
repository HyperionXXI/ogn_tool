from __future__ import annotations

import pandas as pd

from .contracts import NetworkMetrics, ensure_metrics
from .station_removal_simulation import simulate_station_removal


EMPTY_COLUMNS = [
    "station_id",
    "aircraft_lost",
    "coverage_loss_ratio",
    "spof_score",
    "network_status_after_removal",
    "spof_level",
    "notes",
]


def detect_single_points_of_failure(
    network_metrics: NetworkMetrics | None,
    *,
    coverage_loss_threshold: float = 0.25,
) -> pd.DataFrame:
    """Identify stations whose removal would create structural network failure.

    This intelligence-layer detector consumes the canonical visibility matrix
    and the station removal simulation outputs. It does not recompute RF or
    network metrics.
    """
    metrics = ensure_metrics(network_metrics)
    visibility = metrics.get("visibility") or {}
    matrix = visibility.get("matrix") if isinstance(visibility, dict) else None

    if not isinstance(matrix, pd.DataFrame) or matrix.empty:
        return pd.DataFrame(columns=EMPTY_COLUMNS)

    required_cols = {"src", "igate"}
    if not required_cols.issubset(matrix.columns):
        raise ValueError("visibility['matrix'] must contain columns: src, igate")

    stations = sorted({str(station) for station in matrix["igate"].dropna().astype(str).tolist()})
    rows: list[dict] = []

    for station_id in stations:
        sim = simulate_station_removal(station_id, metrics)
        coverage_loss_ratio = float(sim.get("coverage_loss_ratio", 0.0) or 0.0)
        aircraft_lost = int(sim.get("aircraft_lost", 0) or 0)
        spof_score = coverage_loss_ratio * aircraft_lost
        status = str(sim.get("network_status_after_removal") or "GOOD")

        if coverage_loss_ratio >= coverage_loss_threshold:
            spof_level = "HIGH"
            notes = "network critical if removed"
        elif spof_score >= 5.0:
            spof_level = "MEDIUM"
            notes = "significant aircraft loss"
        else:
            spof_level = "LOW"
            notes = "redundant or low impact"

        rows.append(
            {
                "station_id": station_id,
                "aircraft_lost": aircraft_lost,
                "coverage_loss_ratio": coverage_loss_ratio,
                "spof_score": spof_score,
                "network_status_after_removal": status,
                "spof_level": spof_level,
                "notes": notes,
            }
        )

    if not rows:
        return pd.DataFrame(columns=EMPTY_COLUMNS)

    result = pd.DataFrame(rows)
    result = result.sort_values(
        ["spof_score", "coverage_loss_ratio", "aircraft_lost", "station_id"],
        ascending=[False, False, False, True],
    ).reset_index(drop=True)
    return result
