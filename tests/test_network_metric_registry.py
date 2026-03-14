from __future__ import annotations

from ogn_tool.analysis.network_metric_registry import NETWORK_METRIC_REGISTRY


def test_network_metric_registry_contains_critical_metrics() -> None:
    for key in [
        "visibility",
        "network_summary",
        "station_dominance",
        "network_redundancy",
        "network_confidence",
        "station_angular_entropy",
        "coverage_gaps",
    ]:
        assert key in NETWORK_METRIC_REGISTRY


def test_network_metric_registry_groups_are_stable() -> None:
    assert NETWORK_METRIC_REGISTRY["visibility"]["group"] == "network"
    assert NETWORK_METRIC_REGISTRY["station_dominance"]["group"] == "stations"
    assert NETWORK_METRIC_REGISTRY["station_redundancy_planner"]["group"] == "planning"
    assert NETWORK_METRIC_REGISTRY["station_angular_entropy"]["group"] == "shadow"
    assert NETWORK_METRIC_REGISTRY["coverage_gaps"]["group"] == "coverage"
