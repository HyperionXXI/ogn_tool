from __future__ import annotations

from ogn_tool.kernel.visibility_metrics import compute_visibility_metrics
from ogn_tool.intelligence.network.station_influence import compute_station_influence
from ogn_tool.intelligence.network.station_anomaly_detection import detect_station_anomalies
from ogn_tool.intelligence.network.network_robustness_metrics import compute_station_removal_impact



def assemble_network_metrics(base_metrics, dataset) -> dict:
    """Assemble the base network metrics layer.

    This function enriches the graph-derived base metrics with the additional
    first-layer network metrics computed directly from the raw observations.

    The returned dictionary forms the base metrics surface used by higher-level
    intelligence, diagnostics and planning modules.

    No intelligence or planning metrics are included here.
    """
    metrics = dict(base_metrics or {})
    metrics['visibility'] = compute_visibility_metrics(dataset.observations)
    metrics['station_influence'] = compute_station_influence(metrics)
    metrics['station_anomalies'] = detect_station_anomalies(metrics)
    metrics['network_robustness'] = compute_station_removal_impact(metrics)
    return metrics


__all__ = ['assemble_network_metrics']
