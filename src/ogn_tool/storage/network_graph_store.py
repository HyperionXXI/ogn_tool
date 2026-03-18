from __future__ import annotations

import json
import os
from pathlib import Path

from ogn_tool.kernel.graph_metrics import compute_graph_metrics
from ogn_tool.analysis.network_graph.rf_graph_builder import build_rf_graph as build_graph
from ogn_tool.models.network_graph_model import NetworkGraph


def incremental_update(graph: NetworkGraph | dict | None, observations) -> NetworkGraph:
    """Merge new observation-derived graph data into an existing graph."""
    existing_graph = graph if isinstance(graph, NetworkGraph) else NetworkGraph.from_dict(graph)
    new_graph = build_graph(observations)
    if not existing_graph.nodes and not existing_graph.edges:
        return new_graph

    existing_nodes = existing_graph.to_dict().get("nodes") or []
    existing_edges = existing_graph.to_dict().get("edges") or []
    new_nodes = new_graph.to_dict().get("nodes") or []
    new_edges = new_graph.to_dict().get("edges") or []

    node_map: dict[tuple[str, str], dict] = {}
    for node in existing_nodes + new_nodes:
        key = (str(node.get("type")), str(node.get("id")))
        merged = dict(node_map.get(key, {}))
        merged.update(node)
        node_map[key] = merged

    edge_map: dict[tuple[str, str, str], dict] = {}
    for edge in existing_edges:
        key = (str(edge.get("source")), str(edge.get("target")), str(edge.get("type", edge.get("relation"))))
        edge_map[key] = dict(edge)
    for edge in new_edges:
        key = (str(edge.get("source")), str(edge.get("target")), str(edge.get("type", edge.get("relation"))))
        merged = dict(edge_map.get(key, {}))
        merged.update(edge)
        merged["weight"] = float(edge_map.get(key, {}).get("weight", 0)) + float(edge.get("weight", 0))
        edge_map[key] = merged

    merged_graph = NetworkGraph.from_dict(
        {
            "nodes": list(node_map.values()),
            "edges": list(edge_map.values()),
            "metrics": {},
        }
    )
    merged_graph.metrics = compute_graph_metrics(merged_graph)
    return merged_graph


class NetworkGraphStore:
    def __init__(self):
        self.graph: NetworkGraph | None = None
        self.path = Path(os.getenv("OGN_NETWORK_GRAPH_STORE", "network_graph_store.json"))

    def load(self):
        if not self.path.exists():
            return None
        self.graph = NetworkGraph.from_dict(json.loads(self.path.read_text(encoding="utf-8")))
        return self.graph

    def save(self):
        if self.graph is None:
            return None
        self.path.write_text(json.dumps(self.graph.to_dict(), indent=2), encoding="utf-8")
        return self.path

    def update_from_observations(self, observations):
        if self.graph is None:
            self.graph = build_graph(observations)
        else:
            self.graph = incremental_update(self.graph, observations)
        return self.graph


__all__ = ["NetworkGraphStore", "incremental_update", "build_graph"]
