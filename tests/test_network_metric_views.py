from __future__ import annotations

import pandas as pd

from ogn_tool.analysis.network_metric_views import (
    network_confidence_level,
    network_redundancy_level,
    shadow_risk_level,
    station_dependency_level,
)


def test_network_confidence_level() -> None:
    metrics = {"network_confidence": {"confidence_score": 0.9}}

    assert network_confidence_level(metrics) == "excellent"


def test_network_redundancy_level() -> None:
    metrics = {"network_redundancy": {"redundancy_score": 0.72}}

    assert network_redundancy_level(metrics) == "high"


def test_shadow_risk_level() -> None:
    metrics = {"shadow_risk_scores": {"S1": 0.8}}

    assert shadow_risk_level(metrics, "S1") == "high"
    assert shadow_risk_level(metrics, "S2") is None


def test_station_dependency_level() -> None:
    metrics = {
        "station_dependency": pd.DataFrame(
            [
                {"station_id": "S1", "dependency_strength": 0.8},
                {"station_id": "S2", "dependency_strength": 0.2},
            ]
        )
    }

    assert station_dependency_level(metrics, "S1") == "critical"
    assert station_dependency_level(metrics, "S2") == "normal"
    assert station_dependency_level(metrics, "S3") is None
