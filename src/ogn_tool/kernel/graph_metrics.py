from __future__ import annotations

from collections import defaultdict

import pandas as pd

from ogn_tool.models.network_graph_model import NetworkGraph


def _as_graph_dict(graph) -> dict:
    if isinstance(graph, NetworkGraph):
        return graph.to_dict()
    return graph or {"nodes": [], "edges": [], "metrics": {}}


def compute_graph_metrics(graph: dict | NetworkGraph) -> dict:
    """
    Compute lightweight graph metrics for RF intelligence.
    """

    graph_dict = _as_graph_dict(graph)
    nodes = graph_dict.get("nodes") or []
    edges = graph_dict.get("edges") or []

    station_to_aircraft: dict[str, set[str]] = defaultdict(set)
    station_to_grid: dict[str, set[str]] = defaultdict(set)
    grid_to_station: dict[str, set[str]] = defaultdict(set)
    aircraft_to_station: dict[str, set[str]] = defaultdict(set)

    for edge in edges:
        source = str(edge.get("source"))
        target = str(edge.get("target"))
        edge_type = edge.get("type", edge.get("relation"))
        if not source or not target:
            continue
        if edge_type == "reception":
            station_to_aircraft[source].add(target)
            aircraft_to_station[target].add(source)
        elif edge_type == "coverage":
            station_to_grid[source].add(target)
            grid_to_station[target].add(source)

    node_df = pd.DataFrame(nodes) if nodes else pd.DataFrame(columns=["id", "type"])
    station_nodes = node_df[node_df.get("type").eq("station")] if not node_df.empty and "type" in node_df.columns else pd.DataFrame()
    aircraft_nodes = node_df[node_df.get("type").eq("aircraft")] if not node_df.empty and "type" in node_df.columns else pd.DataFrame()
    grid_nodes = node_df[node_df.get("type").eq("grid_cell")] if not node_df.empty and "type" in node_df.columns else pd.DataFrame()

    station_importance = {}
    station_ids = set(station_to_aircraft) | set(station_to_grid)
    for station_id in sorted(station_ids):
        aircraft_links = len(station_to_aircraft.get(station_id, set()))
        grid_links = len(station_to_grid.get(station_id, set()))
        importance_score = float((2 * aircraft_links) + grid_links)
        station_importance[station_id] = {
            "aircraft_links": aircraft_links,
            "grid_links": grid_links,
            "importance_score": importance_score,
        }

    blind_zone_nodes = sorted(grid_id for grid_id, stations in grid_to_station.items() if len(stations) <= 1)
    connectivity = {
        "node_count": int(len(nodes)),
        "edge_count": int(len(edges)),
        "station_count": int(len(station_nodes)),
        "aircraft_count": int(len(aircraft_nodes)),
        "grid_cell_count": int(len(grid_nodes)),
        "connected_station_count": int(len(station_ids)),
    }
    redundancy = {
        "aircraft_redundancy_mean": float(
            pd.Series([len(stations) for stations in aircraft_to_station.values()], dtype="float64").mean()
        )
        if aircraft_to_station
        else 0.0,
        "coverage_redundancy_mean": float(
            pd.Series([len(stations) for stations in grid_to_station.values()], dtype="float64").mean()
        )
        if grid_to_station
        else 0.0,
    }

    return {
        "connectivity": connectivity,
        "redundancy": redundancy,
        "blind_zones": {
            "count": int(len(blind_zone_nodes)),
            "grid_cells": blind_zone_nodes,
        },
        "station_importance": station_importance,
    }



def compute_network_evolution_metrics(graph: dict | NetworkGraph, previous_graph: dict | NetworkGraph | None) -> dict:
    current = compute_graph_metrics(graph)
    previous = compute_graph_metrics(previous_graph or {"nodes": [], "edges": []})

    current_blind = (current.get("blind_zones") or {}).get("count", 0)
    previous_blind = (previous.get("blind_zones") or {}).get("count", 0)
    current_redundancy = (current.get("redundancy") or {}).get("coverage_redundancy_mean", 0.0)
    previous_redundancy = (previous.get("redundancy") or {}).get("coverage_redundancy_mean", 0.0)
    current_coverage = (current.get("connectivity") or {}).get("grid_cell_count", 0)
    previous_coverage = (previous.get("connectivity") or {}).get("grid_cell_count", 0)

    current_importance = current.get("station_importance") or {}
    previous_importance = previous.get("station_importance") or {}
    importance_change = {}
    for station_id in sorted(set(current_importance) | set(previous_importance)):
        cur = float((current_importance.get(station_id) or {}).get("importance_score", 0.0))
        prev = float((previous_importance.get(station_id) or {}).get("importance_score", 0.0))
        importance_change[station_id] = cur - prev

    return {
        "coverage_growth": int(current_coverage - previous_coverage),
        "station_importance_change": importance_change,
        "redundancy_change": float(current_redundancy - previous_redundancy),
        "blind_zone_change": int(current_blind - previous_blind),
    }
