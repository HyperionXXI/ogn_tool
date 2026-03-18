from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from ogn_tool.models.network_graph_model import NetworkEdge, NetworkGraph, NetworkNode

from ogn_tool.kernel.coverage_graph import build_coverage_graph
from ogn_tool.kernel.graph_metrics import compute_graph_metrics
from ogn_tool.kernel.station_graph import compute_station_aircraft_links


def _observations_to_frame(observations) -> pd.DataFrame:
    if observations is None:
        return pd.DataFrame(columns=["station_id", "aircraft_id", "lat", "lon", "altitude_m"])
    if isinstance(observations, dict):
        vectors = observations.get("vectors")
        if vectors is not None and len(vectors) > 0:
            observations = vectors
        else:
            observations = observations.get("distance_df")
    if isinstance(observations, pd.DataFrame):
        df = observations.copy()
    elif isinstance(observations, Iterable) and not isinstance(observations, (str, bytes, dict)):
        rows = []
        for obs in observations:
            rows.append(
                {
                    "station_id": getattr(obs, "station_id", None),
                    "aircraft_id": getattr(obs, "aircraft_id", None),
                    "lat": getattr(obs, "lat", None),
                    "lon": getattr(obs, "lon", None),
                    "altitude_m": getattr(obs, "altitude_m", None),
                }
            )
        df = pd.DataFrame(rows)
    else:
        df = pd.DataFrame(columns=["station_id", "aircraft_id", "lat", "lon", "altitude_m"])

    if "station_id" not in df.columns and "igate" in df.columns:
        df["station_id"] = df["igate"]
    if "aircraft_id" not in df.columns and "src" in df.columns:
        df["aircraft_id"] = df["src"]
    if "altitude_m" not in df.columns:
        if "altitude" in df.columns:
            df["altitude_m"] = df["altitude"]
        elif "alt" in df.columns:
            df["altitude_m"] = df["alt"]
        else:
            df["altitude_m"] = pd.NA
    for col in ["station_id", "aircraft_id", "lat", "lon", "altitude_m"]:
        if col not in df.columns:
            df[col] = pd.NA
    return df[["station_id", "aircraft_id", "lat", "lon", "altitude_m"]].copy()


def build_rf_graph(observations, grid_size_deg: float = 0.05) -> NetworkGraph:
    """
    Build a mixed RF graph with stations, aircraft positions and coverage cells.
    """

    obs_df = _observations_to_frame(observations)
    station_aircraft = compute_station_aircraft_links(obs_df)
    station_coverage = build_coverage_graph(obs_df, grid_size_deg=grid_size_deg)

    nodes: list[NetworkNode] = []
    edges: list[NetworkEdge] = []
    seen_nodes: set[tuple[str, str]] = set()

    def add_node(node_id: str, node_type: str, **attrs) -> None:
        key = (node_type, str(node_id))
        if key in seen_nodes:
            return
        seen_nodes.add(key)
        lat = attrs.pop("lat", None)
        lon = attrs.pop("lon", None)
        altitude = attrs.pop("altitude_m", None)
        if altitude is None:
            altitude = attrs.pop("altitude", None)
        clean_attrs = {k: v for k, v in attrs.items() if pd.notna(v)}
        node = NetworkNode(
            id=str(node_id),
            type=node_type,
            lat=None if pd.isna(lat) else lat,
            lon=None if pd.isna(lon) else lon,
            altitude=None if pd.isna(altitude) else altitude,
            attributes=clean_attrs or None,
        )
        nodes.append(node)

    for row in station_aircraft.to_dict(orient="records"):
        station_id = str(row["station_id"])
        aircraft_id = str(row["aircraft_id"])
        add_node(station_id, "station")
        add_node(
            aircraft_id,
            "aircraft",
            lat=row.get("aircraft_lat"),
            lon=row.get("aircraft_lon"),
            altitude_m=row.get("aircraft_altitude_m"),
        )
        edges.append(
            NetworkEdge(
                source=station_id,
                target=aircraft_id,
                relation="reception",
                weight=float(row.get("observations", 0) or 0),
            )
        )

    for row in station_coverage.to_dict(orient="records"):
        station_id = str(row["station_id"])
        grid_id = str(row["grid_id"])
        add_node(station_id, "station")
        add_node(
            grid_id,
            "grid_cell",
            lat=row.get("grid_lat"),
            lon=row.get("grid_lon"),
            grid_lat=row.get("grid_lat"),
            grid_lon=row.get("grid_lon"),
        )
        edges.append(
            NetworkEdge(
                source=station_id,
                target=grid_id,
                relation="coverage",
                weight=float(row.get("observations", 0) or 0),
            )
        )

    graph = NetworkGraph(nodes=nodes, edges=edges, metrics={})
    graph.metrics = compute_graph_metrics(graph)
    return graph
