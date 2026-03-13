from __future__ import annotations

from ogn_tool.analysis.intelligence.station_planner import suggest_station_locations
from ogn_tool.analysis.network_graph import network_events, network_timeseries
from ogn_tool.analysis.network_graph.graph_metrics import compute_network_evolution_metrics
from ogn_tool.engine import network_graph_engine


def run_network_graph_stage(dataset, previous_graph=None) -> dict:
    graph_result = network_graph_engine.build_graph(dataset.observations)
    metrics = network_graph_engine.compute_network_metrics(graph_result)
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
