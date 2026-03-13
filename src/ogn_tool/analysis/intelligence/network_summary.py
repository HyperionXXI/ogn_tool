from __future__ import annotations

from .contracts import NetworkMetrics, ensure_metrics


def compute_network_summary(network_metrics: NetworkMetrics | None) -> dict:
    """Build a compact operator-facing summary of network health.

    This is an intelligence-layer synthesis over existing network metrics.
    It does not recompute low-level network metrics.
    """
    network_metrics = ensure_metrics(network_metrics)
    station_health = network_metrics.get("station_health")
    visibility = network_metrics.get("visibility") or {}
    robustness = network_metrics.get("network_robustness")

    critical_station_count = 0
    warning_station_count = 0
    top_critical_station = None

    if hasattr(station_health, "empty") and not station_health.empty and "health_status" in station_health.columns:
        critical_station_count = int((station_health["health_status"] == "CRITICAL").sum())
        warning_station_count = int((station_health["health_status"] == "WARNING").sum())

    if hasattr(robustness, "empty") and not robustness.empty and {"station_id", "impact_score"}.issubset(robustness.columns):
        ranked = robustness.sort_values("impact_score", ascending=False)
        if not ranked.empty:
            top_critical_station = str(ranked.iloc[0]["station_id"])
    elif hasattr(station_health, "empty") and not station_health.empty and "station_id" in station_health.columns:
        ranked = station_health.sort_values(["health_status", "impact_score", "influence_score"], ascending=[False, False, False])
        if not ranked.empty:
            top_critical_station = str(ranked.iloc[0]["station_id"])

    summary = visibility.get("summary") if isinstance(visibility, dict) else {}
    single_station_ratio = float((summary or {}).get("single_station_ratio", 0.0) or 0.0)
    mean_stations_per_aircraft = float((summary or {}).get("mean_stations_per_aircraft", 0.0) or 0.0)

    if critical_station_count > 0:
        network_status = "DEGRADED"
        notes = "network contains at least one critical station"
    elif warning_station_count > 2 or single_station_ratio > 0.4:
        network_status = "WARNING"
        notes = "network shows warning-level fragility or limited redundancy"
    else:
        network_status = "GOOD"
        notes = "network appears healthy under current heuristic diagnostics"

    return {
        "network_status": network_status,
        "critical_station_count": critical_station_count,
        "warning_station_count": warning_station_count,
        "single_station_ratio": single_station_ratio,
        "mean_stations_per_aircraft": mean_stations_per_aircraft,
        "top_critical_station": top_critical_station,
        "notes": notes,
    }
