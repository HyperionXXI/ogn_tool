from __future__ import annotations

import pandas as pd

from .contracts import NetworkMetrics, ensure_metrics
from .station_removal_simulation import simulate_station_removal


EMPTY_COLUMNS = [
    "target_station",
    "coverage_loss",
    "aircraft_lost",
    "priority",
    "status_after_removal",
    "notes",
]


def plan_redundancy_improvements(
    network_metrics: NetworkMetrics,
    max_candidates: int = 10,
) -> pd.DataFrame:
    """Rank stations whose loss would most justify adding redundancy.

    This intelligence-layer planner consumes existing visibility metrics and
    station removal simulations. It does not recompute RF or network metrics.
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

    for station in stations:
        sim = simulate_station_removal(station, metrics)
        coverage_loss = float(sim.get("coverage_loss_ratio", 0.0) or 0.0)
        aircraft_lost = int(sim.get("aircraft_lost", 0) or 0)
        priority = coverage_loss * aircraft_lost

        if coverage_loss > 0.25:
            notes = "high removal impact"
        elif coverage_loss > 0.10:
            notes = "moderate redundancy need"
        else:
            notes = "low priority"

        rows.append(
            {
                "target_station": station,
                "coverage_loss": coverage_loss,
                "aircraft_lost": aircraft_lost,
                "priority": priority,
                "status_after_removal": sim.get("network_status_after_removal", "GOOD"),
                "notes": notes,
            }
        )

    if not rows:
        return pd.DataFrame(columns=EMPTY_COLUMNS)

    result = pd.DataFrame(rows)
    result = result.sort_values(["priority", "coverage_loss", "aircraft_lost", "target_station"], ascending=[False, False, False, True])
    return result.head(max_candidates).reset_index(drop=True)
