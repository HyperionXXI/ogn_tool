from __future__ import annotations

NETWORK_METRIC_REGISTRY = {
    "visibility": {"group": "network"},
    "station_influence": {"group": "stations"},
    "station_anomalies": {"group": "stations"},
    "network_robustness": {"group": "network"},
    "station_health": {"group": "stations"},
    "network_summary": {"group": "network"},
    "station_dominance": {"group": "stations"},
    "station_dependency": {"group": "stations"},
    "network_redundancy": {"group": "network"},
    "network_confidence": {"group": "network"},
    "spof": {"group": "network"},
    "station_redundancy_planner": {"group": "planning"},
    "station_angular_entropy": {"group": "shadow"},
    "shadow_risk_scores": {"group": "shadow"},
    "coverage_gaps": {"group": "coverage"},
    "coverage_gap_priorities": {"group": "coverage"},
    "station_addition_simulation": {"group": "planning"},
}


__all__ = ["NETWORK_METRIC_REGISTRY"]
