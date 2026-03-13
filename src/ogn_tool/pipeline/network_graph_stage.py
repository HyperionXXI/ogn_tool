from __future__ import annotations

import pandas as pd

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
from ogn_tool.analysis.network_graph import network_events, network_timeseries
from ogn_tool.analysis.network_graph.graph_metrics import compute_network_evolution_metrics
from ogn_tool.engine import network_graph_engine


def _build_candidate_grid(observations, step_deg: float = 0.05, max_points: int = 400) -> pd.DataFrame:
    if observations is None:
        return pd.DataFrame(columns=["lat", "lon"])

    if isinstance(observations, dict):
        vectors = observations.get("vectors")
        if vectors is not None and len(vectors) > 0:
            rows = [
                {"lat": getattr(obs, "lat", None), "lon": getattr(obs, "lon", None)}
                for obs in vectors
            ]
            df = pd.DataFrame(rows)
        else:
            df = observations.get("distance_df")
            if df is None:
                df = pd.DataFrame(columns=["lat", "lon"])
            else:
                df = pd.DataFrame(df).copy()
    elif isinstance(observations, pd.DataFrame):
        df = observations.copy()
    else:
        rows = [
            {"lat": getattr(obs, "lat", None), "lon": getattr(obs, "lon", None)}
            for obs in observations
        ]
        df = pd.DataFrame(rows)

    if df is None or df.empty or not {"lat", "lon"}.issubset(df.columns):
        return pd.DataFrame(columns=["lat", "lon"])

    df = df[["lat", "lon"]].copy()
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df.dropna(subset=["lat", "lon"])
    if df.empty:
        return pd.DataFrame(columns=["lat", "lon"])

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
