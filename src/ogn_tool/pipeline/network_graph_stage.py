from __future__ import annotations

import pandas as pd

from ogn_tool.analysis.intelligence import (
    compute_network_summary,
    compute_station_dependency,
    compute_station_health,
    detect_coverage_gaps,
    detect_single_points_of_failure,
    plan_redundancy_improvements,
    prioritize_coverage_gaps,
    simulate_station_addition,
)
from ogn_tool.analysis.intelligence.station_planner import suggest_station_locations
from ogn_tool.analysis.network_metrics import (
    compute_station_influence,
    compute_station_removal_impact,
    compute_visibility_metrics,
    detect_station_anomalies,
)
from ogn_tool.analysis.network_metrics.station_placement import (
    compute_optimal_station_locations,
)
from ogn_tool.analysis.network_metrics.validate import validate_network_metrics
from ogn_tool.analysis.network_graph import network_events, network_timeseries
from ogn_tool.analysis.network_graph.graph_metrics import compute_network_evolution_metrics
from ogn_tool.analysis.normalization.observation_rows import observations_to_rows
from ogn_tool.engine import network_graph_engine


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


def _observations_to_frame(observations) -> pd.DataFrame:
    if observations is None:
        return pd.DataFrame(columns=["station_id", "lat", "lon"])

    if isinstance(observations, dict):
        vectors = observations.get("vectors")
        if vectors is not None and len(vectors) > 0:
            rows = observations_to_rows(vectors)
            df = pd.DataFrame(rows)
        else:
            distance_df = observations.get("distance_df")
            df = pd.DataFrame(distance_df).copy() if distance_df is not None else pd.DataFrame()
    elif isinstance(observations, pd.DataFrame):
        df = observations.copy()
    else:
        df = pd.DataFrame(observations_to_rows(observations))

    if df.empty:
        return pd.DataFrame(columns=["station_id", "lat", "lon"])

    if "station_id" not in df.columns and "igate" in df.columns:
        df["station_id"] = df["igate"]

    for column in ["station_id", "lat", "lon"]:
        if column not in df.columns:
            df[column] = pd.NA

    df = df[["station_id", "lat", "lon"]].copy()
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df.dropna(subset=["station_id", "lat", "lon"])
    return df.reset_index(drop=True)


def _build_candidate_grid(observations, step_deg: float = 0.05, max_points: int = 400) -> pd.DataFrame:
    df = _observations_to_frame(observations)
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
    metrics = network_graph_engine.compute_network_metrics(graph_result)
    metrics = dict(metrics or {})
    metrics["visibility"] = compute_visibility_metrics(dataset.observations)
    metrics["station_influence"] = compute_station_influence(metrics)
    metrics["station_anomalies"] = detect_station_anomalies(metrics)
    metrics["network_robustness"] = compute_station_removal_impact(metrics)

    candidate_grid = _build_candidate_grid(dataset.observations)
    if candidate_grid.empty:
        placement = pd.DataFrame()
    else:
        placement = compute_optimal_station_locations(metrics, candidate_grid)
    metrics["station_placement"] = placement
    metrics["station_health"] = compute_station_health(metrics)
    metrics["network_summary"] = compute_network_summary(metrics)
    metrics["station_dependency"] = compute_station_dependency(metrics)
    metrics["spof"] = detect_single_points_of_failure(metrics)
    metrics["station_redundancy_planner"] = plan_redundancy_improvements(metrics)

    observations_df = _observations_to_frame(dataset.observations)
    if observations_df.empty:
        metrics["coverage_gaps"] = pd.DataFrame(columns=EMPTY_GAP_COLUMNS)
        metrics["coverage_gap_priorities"] = pd.DataFrame(columns=EMPTY_GAP_PRIORITY_COLUMNS)
        metrics["station_addition_simulation"] = pd.DataFrame(columns=EMPTY_ADDITION_COLUMNS)
    else:
        coverage_gaps = detect_coverage_gaps(observations_df)
        coverage_gap_priorities = prioritize_coverage_gaps(coverage_gaps)
        if coverage_gap_priorities.empty:
            station_addition = pd.DataFrame(columns=EMPTY_ADDITION_COLUMNS)
        else:
            station_addition = simulate_station_addition(
                coverage_gap_priorities[["lat", "lon"]],
                observations_df,
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
    }


__all__ = ["run_network_graph_stage"]
