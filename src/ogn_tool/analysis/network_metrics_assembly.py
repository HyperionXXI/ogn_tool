from __future__ import annotations

from ogn_tool.analysis.network_metrics import (
    compute_station_influence,
    compute_station_removal_impact,
    compute_visibility_metrics,
    detect_station_anomalies,
)
from ogn_tool.engine import network_graph_engine


def assemble_network_metrics(graph_result, dataset) -> dict:
    """Assemble the base network metrics layer.

    This function aggregates metrics derived directly from:
        - the computed network graph
        - the raw observation dataset

    The returned dictionary forms the base metrics surface used
    by higher-level intelligence, diagnostics and planning modules.

    No intelligence or planning metrics are included here.
    """
    metrics = network_graph_engine.compute_network_metrics(graph_result) or {}
    metrics = dict(metrics)
    metrics["visibility"] = compute_visibility_metrics(dataset.observations)
    metrics["station_influence"] = compute_station_influence(metrics)
    metrics["station_anomalies"] = detect_station_anomalies(metrics)
    metrics["network_robustness"] = compute_station_removal_impact(metrics)
    return metrics


__all__ = ["assemble_network_metrics"]
