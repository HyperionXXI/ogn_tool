from __future__ import annotations

import pandas as pd

from .contracts import NetworkMetrics, ensure_metrics


def _interpret_redundancy(score: float) -> str:
    if score >= 0.85:
        return "very high redundancy"
    if score >= 0.70:
        return "good redundancy"
    if score >= 0.50:
        return "moderate redundancy"
    if score >= 0.30:
        return "fragile network"
    return "critical network"


def compute_network_redundancy_score(network_metrics: NetworkMetrics | None) -> dict:
    metrics = ensure_metrics(network_metrics)

    visibility = metrics.get("visibility") if isinstance(metrics.get("visibility"), dict) else {}
    visibility_summary = visibility.get("summary") if isinstance(visibility, dict) else {}
    if not isinstance(visibility_summary, dict):
        visibility_summary = {}

    dominance = metrics.get("station_dominance")
    dependency = metrics.get("station_dependency")
    _ = metrics.get("network_robustness")

    mean_stations_per_aircraft = float(visibility_summary.get("mean_stations_per_aircraft") or 0.0)
    single_station_ratio = float(visibility_summary.get("single_station_ratio") or 0.0)

    mean_dominance_ratio = 0.0
    if isinstance(dominance, pd.DataFrame) and not dominance.empty and "dominance_ratio" in dominance.columns:
        mean_dominance_ratio = float(pd.to_numeric(dominance["dominance_ratio"], errors="coerce").fillna(0.0).mean())

    high_dependency_station_ratio = 0.0
    if isinstance(dependency, pd.DataFrame) and not dependency.empty and "dependency_strength" in dependency.columns:
        strengths = pd.to_numeric(dependency["dependency_strength"], errors="coerce").fillna(0.0)
        high_dependency_station_ratio = float((strengths >= 0.7).mean())

    mean_stations_per_aircraft_norm = min(mean_stations_per_aircraft / 4.0, 1.0)
    score = (
        0.35 * mean_stations_per_aircraft_norm
        + 0.25 * (1.0 - single_station_ratio)
        + 0.20 * (1.0 - mean_dominance_ratio)
        + 0.20 * (1.0 - high_dependency_station_ratio)
    )
    score = min(max(float(score), 0.0), 1.0)

    return {
        "redundancy_score": score,
        "single_station_ratio": single_station_ratio,
        "mean_stations_per_aircraft": mean_stations_per_aircraft,
        "mean_dominance_ratio": mean_dominance_ratio,
        "high_dependency_station_ratio": high_dependency_station_ratio,
        "interpretation": _interpret_redundancy(score),
    }
