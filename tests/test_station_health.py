from __future__ import annotations

import pandas as pd

from ogn_tool.analysis.intelligence.station_health import compute_station_health


def test_compute_station_health_empty():
    result = compute_station_health({})
    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == [
        "station_id",
        "health_status",
        "influence_score",
        "impact_score",
        "anomaly_count",
        "primary_anomaly",
        "notes",
    ]
    assert result.empty


def test_compute_station_health_prioritizes_critical_station():
    network_metrics = {
        "station_influence": pd.DataFrame([
            {"station_id": "FK50887", "influence_score": 6.5},
            {"station_id": "RAIMEUX", "influence_score": 1.5},
            {"station_id": "LOW", "influence_score": 0.2},
        ]),
        "network_robustness": pd.DataFrame([
            {"station_id": "FK50887", "impact_score": 6.2},
            {"station_id": "RAIMEUX", "impact_score": 1.2},
            {"station_id": "LOW", "impact_score": 0.1},
        ]),
        "station_anomalies": pd.DataFrame([
            {"station_id": "FK50887", "anomaly_type": "critical_single_station", "severity": "high", "description": "critical", "metric_value": 0.5},
            {"station_id": "RAIMEUX", "anomaly_type": "weak_station", "severity": "medium", "description": "weak", "metric_value": 1.0},
        ]),
    }

    result = compute_station_health(network_metrics)

    assert list(result["station_id"]) == ["FK50887", "RAIMEUX", "LOW"]
    fk = result[result["station_id"] == "FK50887"].iloc[0]
    raimeux = result[result["station_id"] == "RAIMEUX"].iloc[0]
    low = result[result["station_id"] == "LOW"].iloc[0]

    assert fk["health_status"] == "CRITICAL"
    assert fk["anomaly_count"] == 1
    assert fk["primary_anomaly"] == "critical_single_station"

    assert raimeux["health_status"] == "WARNING"
    assert low["health_status"] == "GOOD"
