from __future__ import annotations

import pandas as pd

from .contracts import NetworkMetrics, ensure_metrics

HEALTH_RULES = {
    "CRITICAL": {
        "impact_score_min": 5.0,
        "anomaly_types": {"critical_single_station"},
    },
    "WARNING": {
        "impact_score_min": 1.0,
        "anomaly_types": {"high_redundancy", "weak_station"},
    },
    "GOOD": {},
}


def _build_anomaly_lookup(anomalies: pd.DataFrame | None) -> dict[str, dict]:
    if not isinstance(anomalies, pd.DataFrame) or anomalies.empty or "station_id" not in anomalies.columns:
        return {}

    lookup: dict[str, dict] = {}
    for station_id, group in anomalies.groupby("station_id"):
        group = group.copy()
        group["severity_rank"] = group["severity"].map({"high": 3, "medium": 2, "low": 1}).fillna(0)
        group = group.sort_values(["severity_rank", "anomaly_type"], ascending=[False, True])
        lookup[str(station_id)] = {
            "count": int(len(group)),
            "primary": str(group.iloc[0].get("anomaly_type") or ""),
            "types": {str(v) for v in group.get("anomaly_type", pd.Series(dtype=object)).dropna().astype(str).tolist()},
        }
    return lookup


def compute_station_health(network_metrics: NetworkMetrics | None) -> pd.DataFrame:
    """Build an operator-facing station health table from network metrics.

    This is an intelligence-layer interpretation of existing network metrics.
    It does not compute new network metrics and should remain a thin,
    explainable synthesis layer.
    """
    network_metrics = ensure_metrics(network_metrics)
    influence = network_metrics.get("station_influence")
    robustness = network_metrics.get("network_robustness")
    anomalies = network_metrics.get("station_anomalies")

    if not isinstance(influence, pd.DataFrame) or influence.empty:
        return pd.DataFrame(columns=[
            "station_id",
            "health_status",
            "influence_score",
            "impact_score",
            "anomaly_count",
            "primary_anomaly",
            "notes",
        ])

    base = influence[["station_id", "influence_score"]].copy() if {"station_id", "influence_score"}.issubset(influence.columns) else pd.DataFrame(columns=["station_id", "influence_score"])
    if base.empty:
        return pd.DataFrame(columns=[
            "station_id",
            "health_status",
            "influence_score",
            "impact_score",
            "anomaly_count",
            "primary_anomaly",
            "notes",
        ])

    if isinstance(robustness, pd.DataFrame) and not robustness.empty and {"station_id", "impact_score"}.issubset(robustness.columns):
        base = base.merge(robustness[["station_id", "impact_score"]], on="station_id", how="left")
    else:
        base["impact_score"] = 0.0

    anomaly_lookup = _build_anomaly_lookup(anomalies)

    rows: list[dict] = []
    for _, row in base.iterrows():
        station_id = str(row.get("station_id"))
        influence_score = float(row.get("influence_score", 0.0) or 0.0)
        impact_score = float(row.get("impact_score", 0.0) or 0.0)
        anomaly_info = anomaly_lookup.get(station_id, {"count": 0, "primary": "", "types": set()})
        anomaly_count = int(anomaly_info["count"])
        primary_anomaly = str(anomaly_info["primary"] or "")

        if primary_anomaly in HEALTH_RULES["CRITICAL"]["anomaly_types"] or impact_score >= HEALTH_RULES["CRITICAL"]["impact_score_min"]:
            health_status = "CRITICAL"
            notes = "station is structurally important or has a critical anomaly"
        elif anomaly_count > 0 or primary_anomaly in HEALTH_RULES["WARNING"]["anomaly_types"] or impact_score >= HEALTH_RULES["WARNING"]["impact_score_min"] or influence_score >= 3.0:
            health_status = "WARNING"
            notes = "station requires attention due to anomalies or structural importance"
        else:
            health_status = "GOOD"
            notes = "station appears healthy under current heuristic diagnostics"

        rows.append({
            "station_id": station_id,
            "health_status": health_status,
            "influence_score": influence_score,
            "impact_score": impact_score,
            "anomaly_count": anomaly_count,
            "primary_anomaly": primary_anomaly,
            "notes": notes,
        })

    result = pd.DataFrame(rows)
    if result.empty:
        return pd.DataFrame(columns=[
            "station_id",
            "health_status",
            "influence_score",
            "impact_score",
            "anomaly_count",
            "primary_anomaly",
            "notes",
        ])

    status_rank = {"CRITICAL": 3, "WARNING": 2, "GOOD": 1}
    result["_status_rank"] = result["health_status"].map(status_rank).fillna(0)
    result = result.sort_values(["_status_rank", "impact_score", "influence_score", "station_id"], ascending=[False, False, False, True]).drop(columns=["_status_rank"]).reset_index(drop=True)
    return result
