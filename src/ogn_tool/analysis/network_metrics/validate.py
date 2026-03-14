from __future__ import annotations

import pandas as pd


REQUIRED_NETWORK_METRICS = {
    "visibility",
    "station_influence",
    "station_anomalies",
    "network_robustness",
    "station_placement",
    "station_health",
    "station_dominance",
    "station_angular_entropy",
    "shadow_risk_scores",
    "network_summary",
    "station_dependency",
    "spof",
    "coverage_gaps",
    "coverage_gap_priorities",
    "station_redundancy_planner",
    "station_addition_simulation",
}


DATAFRAME_METRICS = {
    "station_influence",
    "station_anomalies",
    "network_robustness",
    "station_placement",
    "station_health",
    "station_dominance",
    "station_dependency",
    "spof",
    "coverage_gaps",
    "coverage_gap_priorities",
    "station_redundancy_planner",
    "station_addition_simulation",
}


DICT_METRICS = {
    "visibility",
    "station_angular_entropy",
    "shadow_risk_scores",
    "network_summary",
}


OPTIONAL_DICT_METRICS = {
    "network_redundancy",
}


def validate_network_metrics(metrics: dict) -> None:
    if not isinstance(metrics, dict):
        raise RuntimeError("network_metrics must be a dict")

    missing = REQUIRED_NETWORK_METRICS - metrics.keys()
    if missing:
        raise RuntimeError(f"Missing network_metrics keys: {sorted(missing)}")

    for key in DATAFRAME_METRICS:
        value = metrics.get(key)
        if not isinstance(value, pd.DataFrame):
            raise RuntimeError(f"{key} must be a pandas DataFrame")

    for key in DICT_METRICS:
        value = metrics.get(key)
        if not isinstance(value, dict):
            raise RuntimeError(f"{key} must be a dict")

    for key in OPTIONAL_DICT_METRICS:
        if key in metrics and not isinstance(metrics.get(key), dict):
            raise RuntimeError(f"{key} must be a dict when present")
