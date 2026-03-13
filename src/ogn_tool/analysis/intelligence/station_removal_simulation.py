from __future__ import annotations

import pandas as pd

from .contracts import NetworkMetrics, ensure_metrics


def _empty_result(station_id: str) -> dict:
    return {
        "removed_station": station_id,
        "aircraft_total": 0,
        "aircraft_lost": 0,
        "coverage_loss_ratio": 0.0,
        "stations_becoming_critical": [],
        "network_status_after_removal": "GOOD",
        "notes": "no visibility data available",
    }


def simulate_station_removal(
    station_id: str,
    network_metrics: NetworkMetrics | None,
    *,
    max_aircraft: int | None = None,
) -> dict:
    """Simulate the structural impact of losing one station.

    This intelligence-layer function consumes existing visibility metrics.
    It does not recompute RF metrics or rebuild network structures beyond
    a local grouping of the canonical visibility matrix.
    """
    metrics = ensure_metrics(network_metrics)
    visibility = metrics.get("visibility") or {}
    matrix = visibility.get("matrix") if isinstance(visibility, dict) else None

    if not isinstance(matrix, pd.DataFrame) or matrix.empty:
        return _empty_result(station_id)

    required_columns = {"src", "igate"}
    if not required_columns.issubset(matrix.columns):
        return _empty_result(station_id)

    grouped = (
        matrix[["src", "igate"]]
        .dropna(subset=["src", "igate"])
        .astype({"src": str, "igate": str})
        .groupby("src")["igate"]
        .agg(lambda values: sorted(set(values.tolist())))
    )

    if grouped.empty:
        return _empty_result(station_id)

    if max_aircraft is not None and max_aircraft > 0:
        grouped = grouped.head(int(max_aircraft))

    total_aircraft = int(len(grouped))
    aircraft_lost = 0
    stations_becoming_critical: set[str] = set()

    for stations in grouped.tolist():
        remaining = [receiver for receiver in stations if receiver != station_id]
        if len(remaining) == 0:
            aircraft_lost += 1
        elif len(remaining) == 1:
            stations_becoming_critical.add(remaining[0])

    coverage_loss_ratio = float(aircraft_lost / total_aircraft) if total_aircraft else 0.0

    if coverage_loss_ratio > 0.25:
        network_status = "CRITICAL"
        notes = "station removal causes major aircraft visibility loss"
    elif coverage_loss_ratio > 0.10:
        network_status = "WARNING"
        notes = "station removal causes noticeable coverage loss"
    else:
        network_status = "GOOD"
        notes = "station removal remains tolerable under current heuristic"

    return {
        "removed_station": station_id,
        "aircraft_total": total_aircraft,
        "aircraft_lost": aircraft_lost,
        "coverage_loss_ratio": coverage_loss_ratio,
        "stations_becoming_critical": sorted(stations_becoming_critical),
        "network_status_after_removal": network_status,
        "notes": notes,
    }
