from __future__ import annotations

# Canonical list of metric families produced by the RF analysis pipeline.

EXPECTED_NETWORK_METRICS = {
    "network_summary",
    "station_angular_entropy",
    "shadow_risk_scores",
    "visibility",
    "station_dominance",
    "station_dependency",
    "network_redundancy",
}

# Optional classification (future use)

EXPECTED_DICT_METRICS = {
    "network_summary",
    "station_angular_entropy",
    "shadow_risk_scores",
}

EXPECTED_DATAFRAME_METRICS = {
    "visibility",
    "station_dominance",
    "station_dependency",
    "network_redundancy",
}


def collect_network_metric_warnings(metrics: dict) -> list[str]:
    warnings: list[str] = []

    for key in sorted(EXPECTED_NETWORK_METRICS):
        if key not in metrics:
            warnings.append(f"{key} not produced by analysis pipeline")

    return warnings
