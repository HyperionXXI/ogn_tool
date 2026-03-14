from __future__ import annotations

from ogn_tool.analysis.intelligence import (
    compute_network_confidence,
    compute_network_redundancy_score,
    compute_network_summary,
    compute_station_dependency,
    compute_station_dominance,
    compute_station_health,
)
from ogn_tool.analysis.observation_views import (
    build_spatial_observation_frame,
    build_visibility_observation_frame,
)


def assemble_network_intelligence(metrics: dict, dataset) -> tuple[dict, object]:
    """Assemble higher-level network intelligence metrics on top of base metrics.

    This function computes the station and network intelligence layer used by
    downstream planning, diagnostics and reporting modules.

    Returns the mutated metrics dictionary together with the canonical spatial
    observation frame already built for downstream reuse in the pipeline stage.
    """
    metrics["station_health"] = compute_station_health(metrics)
    metrics["network_summary"] = compute_network_summary(metrics)

    spatial_observations = build_spatial_observation_frame(dataset.observations)
    dominance_observations = build_visibility_observation_frame(dataset.observations)

    metrics["station_dominance"] = compute_station_dominance(dominance_observations, metrics)
    metrics["station_dependency"] = compute_station_dependency(metrics)
    metrics["network_redundancy"] = compute_network_redundancy_score(metrics)

    confidence_score, confidence_warnings = compute_network_confidence(metrics)
    metrics["network_confidence"] = {"confidence_score": confidence_score}
    if confidence_warnings:
        metrics["_confidence_warnings"] = confidence_warnings

    return metrics, spatial_observations


__all__ = ["assemble_network_intelligence"]
