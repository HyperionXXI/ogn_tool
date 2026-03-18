from __future__ import annotations

import pandas as pd

from ogn_tool.kernel.network_graph_analysis_facade import (
    assemble_network_intelligence,
    assemble_network_metrics,
    build_shadow_observation_frame,
    build_spatial_observation_frame,
    check_intelligence_coherence,
    collect_network_metric_warnings,
    compute_network_evolution_metrics,
    compute_optimal_station_locations,
    compute_shadow_risk_scores,
    compute_station_angular_entropy,
    detect_coverage_gaps,
    detect_single_points_of_failure,
    network_events,
    network_timeseries,
    plan_redundancy_improvements,
    prioritize_coverage_gaps,
    simulate_station_addition,
    suggest_station_locations,
    validate_network_metrics,
)
from ogn_tool.kernel import network_graph_engine


EMPTY_GAP_COLUMNS = ["lat", "lon", "station_count", "gap_level", "notes"]
EMPTY_GAP_PRIORITY_COLUMNS = [
    "lat",
    "lon",
    "station_count",
    "gap_level",
    "priority_score",
    "recommended_action",
    "notes",
]
EMPTY_ADDITION_COLUMNS = [
    "lat",
    "lon",
    "aircraft_supported",
    "coverage_gain",
    "redundancy_gain",
    "priority_score",
    "notes",
]


def _build_candidate_grid(observations, step_deg: float = 0.05, max_points: int = 400) -> pd.DataFrame:
    df = build_spatial_observation_frame(observations)
    if df.empty:
        return pd.DataFrame(columns=["lat", "lon"])

    df = df[["lat", "lon"]].copy()

    min_lat = float(df["lat"].min())
    max_lat = float(df["lat"].max())
    min_lon = float(df["lon"].min())
    max_lon = float(df["lon"].max())

    lat_grid = pd.Series(pd.array([min_lat + i * step_deg for i in range(int((max_lat - min_lat) / step_deg) + 1)], dtype="float64"))
    lon_grid = pd.Series(pd.array([min_lon + i * step_deg for i in range(int((max_lon - min_lon) / step_deg) + 1)], dtype="float64"))

    grid = pd.DataFrame(
        [(lat, lon) for lat in lat_grid for lon in lon_grid],
        columns=["lat", "lon"],
    )

    if grid.empty:
        return pd.DataFrame(columns=["lat", "lon"])
    if len(grid) > max_points:
        grid = grid.sample(max_points, random_state=42).reset_index(drop=True)
    return grid


def run_network_graph_stage(dataset, previous_graph=None) -> dict:
    graph_result = network_graph_engine.build_graph(dataset.observations)
    base_metrics = network_graph_engine.compute_network_metrics(graph_result)
    metrics = assemble_network_metrics(base_metrics, dataset)

    candidate_grid = _build_candidate_grid(dataset.observations)
    if candidate_grid.empty:
        placement = pd.DataFrame()
    else:
        placement = compute_optimal_station_locations(metrics, candidate_grid)
    metrics["station_placement"] = placement

    metrics, spatial_observations = assemble_network_intelligence(metrics, dataset)
    metrics["spof"] = detect_single_points_of_failure(metrics)
    metrics["station_redundancy_planner"] = plan_redundancy_improvements(metrics)

    shadow_observations = build_shadow_observation_frame(dataset.observations)
    metrics["station_angular_entropy"] = compute_station_angular_entropy(shadow_observations)
    metrics["shadow_risk_scores"] = compute_shadow_risk_scores(shadow_observations)

    if spatial_observations.empty:
        metrics["coverage_gaps"] = pd.DataFrame(columns=EMPTY_GAP_COLUMNS)
        metrics["coverage_gap_priorities"] = pd.DataFrame(columns=EMPTY_GAP_PRIORITY_COLUMNS)
        metrics["station_addition_simulation"] = pd.DataFrame(columns=EMPTY_ADDITION_COLUMNS)
    else:
        coverage_gaps = detect_coverage_gaps(spatial_observations)
        coverage_gap_priorities = prioritize_coverage_gaps(coverage_gaps)
        if coverage_gap_priorities.empty:
            station_addition = pd.DataFrame(columns=EMPTY_ADDITION_COLUMNS)
        else:
            station_addition = simulate_station_addition(
                coverage_gap_priorities[["lat", "lon"]],
                spatial_observations,
            )
        metrics["coverage_gaps"] = coverage_gaps
        metrics["coverage_gap_priorities"] = coverage_gap_priorities
        metrics["station_addition_simulation"] = station_addition

    timeseries = network_timeseries.compute_station_activity_timeseries(dataset.observations)
    anomalies = network_events.detect_network_anomalies(timeseries)
    coverage_timeseries = network_timeseries.compute_coverage_timeseries(
        {
            "observations": dataset.observations,
            "graph": graph_result.graph,
        }
    )
    coverage_regressions = network_events.detect_coverage_regressions(coverage_timeseries)
    station_outages = network_events.detect_station_outages(timeseries)
    coverage_grid = getattr(dataset.results, "coverage", None)
    network_evolution = compute_network_evolution_metrics(graph_result.graph, previous_graph)
    station_suggestions = suggest_station_locations(graph_result.graph, coverage_grid)

    contract_warnings = collect_network_metric_warnings(metrics)
    if contract_warnings:
        metrics["_contract_warnings"] = contract_warnings

    coherence_warnings = check_intelligence_coherence(metrics)
    if coherence_warnings:
        metrics["_coherence_warnings"] = coherence_warnings

    validate_network_metrics(metrics)

    return {
        "graph": graph_result,
        "metrics": metrics,
        "timeseries": timeseries,
        "events": {
            "anomalies": anomalies,
            "station_outages": station_outages,
            "coverage_regressions": coverage_regressions,
        },
        "evolution": network_evolution,
        "station_suggestions": station_suggestions,
        "spatial_observations": spatial_observations,
    }


__all__ = ["run_network_graph_stage"]
