from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ogn_tool.engine.network_graph_analysis_facade import build_rf_graph, compute_graph_metrics
from ogn_tool.models.network_graph_model import NetworkGraph


@dataclass
class NetworkGraphResult:
    graph: NetworkGraph
    metrics: dict
    station_links: Any = None
    coverage_links: Any = None


def build_graph(observations) -> NetworkGraphResult:
    graph = build_rf_graph(observations)
    edges = graph.get("edges") or []
    station_links = [edge for edge in edges if edge.get("type") == "reception"]
    coverage_links = [edge for edge in edges if edge.get("type") == "coverage"]
    return NetworkGraphResult(
        graph=graph,
        metrics=graph.get("metrics") or compute_graph_metrics(graph),
        station_links=station_links,
        coverage_links=coverage_links,
    )


def compute_network_metrics(graph) -> dict:
    if isinstance(graph, NetworkGraphResult):
        return graph.metrics
    return compute_graph_metrics(graph)


__all__ = ["NetworkGraphResult", "build_graph", "compute_network_metrics"]
