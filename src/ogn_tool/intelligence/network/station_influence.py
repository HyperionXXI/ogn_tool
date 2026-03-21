from __future__ import annotations

import pandas as pd


def compute_station_influence(network_metrics: dict | None) -> pd.DataFrame:
    """Compute a lightweight station influence score from existing network metrics.

    This is a synthesis metric built from:
    - visibility metrics
    - graph station importance
    - station overlap

    No new heavy algorithm is introduced here; the function only consolidates
    existing network analysis outputs into a stable ranking surface.
    """
    network_metrics = network_metrics or {}

    visibility = network_metrics.get("visibility") or {}
    dependency = visibility.get("dependency")
    overlap = visibility.get("overlap")
    station_importance = network_metrics.get("station_importance") or {}

    stations: set[str] = set(station_importance.keys())

    unique_aircraft_count: dict[str, int] = {}
    single_station_aircraft_count: dict[str, int] = {}
    if isinstance(dependency, pd.DataFrame) and not dependency.empty:
        stations.update(str(v) for v in dependency.get("critical_station_id", pd.Series(dtype=object)).dropna().astype(str).tolist())
        grouped = dependency.groupby("critical_station_id", dropna=True) if "critical_station_id" in dependency.columns else []
        for station_id, group in grouped:
            station_key = str(station_id)
            count = int(len(group))
            unique_aircraft_count[station_key] = count
            single_station_aircraft_count[station_key] = count

    mean_overlap: dict[str, float] = {}
    if isinstance(overlap, pd.DataFrame) and not overlap.empty:
        stations.update(str(v) for v in overlap.index.tolist())
        for station_id in overlap.index:
            row = pd.to_numeric(overlap.loc[station_id], errors="coerce")
            row = row.drop(labels=[station_id], errors="ignore")
            mean_overlap[str(station_id)] = float(row.mean()) if not row.empty else 0.0

    rows = []
    for station_id in sorted(stations):
        importance_info = station_importance.get(station_id) or {}
        graph_importance = float(importance_info.get("importance_score", 0.0) or 0.0)
        unique_count = int(unique_aircraft_count.get(station_id, 0) or 0)
        single_count = int(single_station_aircraft_count.get(station_id, 0) or 0)
        overlap_mean = float(mean_overlap.get(station_id, 0.0) or 0.0)
        aircraft_seen = int(importance_info.get("aircraft_links", 0) or 0)
        redundancy_penalty = overlap_mean
        influence_score = float((2.0 * unique_count) + (3.0 * single_count) + graph_importance - redundancy_penalty)

        rows.append({
            "station_id": station_id,
            "aircraft_seen": aircraft_seen,
            "unique_aircraft_count": unique_count,
            "single_station_aircraft_count": single_count,
            "mean_overlap": overlap_mean,
            "graph_importance": graph_importance,
            "redundancy_penalty": redundancy_penalty,
            "influence_score": influence_score,
        })

    if not rows:
        return pd.DataFrame(columns=[
            "station_id",
            "aircraft_seen",
            "unique_aircraft_count",
            "single_station_aircraft_count",
            "mean_overlap",
            "graph_importance",
            "redundancy_penalty",
            "influence_score",
        ])

    return pd.DataFrame(rows).sort_values("influence_score", ascending=False).reset_index(drop=True)
