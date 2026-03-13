from __future__ import annotations

import pandas as pd


def detect_station_anomalies(network_metrics: dict | None) -> pd.DataFrame:
    """Detect lightweight station anomalies from existing network metrics.

    This consolidates existing signals only; it does not introduce heavy models.
    """
    network_metrics = network_metrics or {}
    visibility = network_metrics.get("visibility") or {}
    influence = network_metrics.get("station_influence")

    if not isinstance(influence, pd.DataFrame) or influence.empty:
        return pd.DataFrame(columns=["station_id", "anomaly_type", "severity", "description", "metric_value"])

    summary = visibility.get("summary") if isinstance(visibility, dict) else {}
    dependency = visibility.get("dependency") if isinstance(visibility, dict) else None

    mean_stations = float((summary or {}).get("mean_stations_per_aircraft", 0.0) or 0.0)
    aircraft_seen_series = pd.to_numeric(influence.get("aircraft_seen"), errors="coerce") if "aircraft_seen" in influence.columns else pd.Series(dtype=float)
    median_aircraft_seen = float(aircraft_seen_series.median()) if not aircraft_seen_series.empty and aircraft_seen_series.notna().any() else 0.0

    rows: list[dict] = []
    for _, row in influence.iterrows():
        station_id = str(row.get("station_id"))
        unique_count = int(row.get("unique_aircraft_count", 0) or 0)
        single_count = int(row.get("single_station_aircraft_count", 0) or 0)
        mean_overlap = float(row.get("mean_overlap", 0.0) or 0.0)
        aircraft_seen = float(row.get("aircraft_seen", 0.0) or 0.0)

        single_ratio = float(single_count / aircraft_seen) if aircraft_seen > 0 else 0.0
        if single_ratio > 0.2:
            severity = "high" if single_ratio > 0.4 else "medium"
            rows.append({
                "station_id": station_id,
                "anomaly_type": "critical_single_station",
                "severity": severity,
                "description": "station is the only receiver for multiple aircraft",
                "metric_value": single_ratio,
            })

        if unique_count < 2 and mean_overlap > max(1.0, mean_stations):
            severity = "medium" if mean_overlap > max(2.0, mean_stations * 1.5) else "low"
            rows.append({
                "station_id": station_id,
                "anomaly_type": "high_redundancy",
                "severity": severity,
                "description": "station shows high overlap with low unique contribution",
                "metric_value": mean_overlap,
            })

        if median_aircraft_seen > 0 and aircraft_seen < median_aircraft_seen * 0.3:
            severity = "high" if aircraft_seen < median_aircraft_seen * 0.15 else "medium"
            rows.append({
                "station_id": station_id,
                "anomaly_type": "weak_station",
                "severity": severity,
                "description": "station sees significantly fewer aircraft than peers",
                "metric_value": aircraft_seen,
            })

    anomalies = pd.DataFrame(rows)
    if anomalies.empty:
        return pd.DataFrame(columns=["station_id", "anomaly_type", "severity", "description", "metric_value"])
    return anomalies.sort_values(["severity", "station_id"], ascending=[True, True]).reset_index(drop=True)
