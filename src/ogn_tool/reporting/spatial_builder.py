from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple

import pandas as pd


def _as_mapping(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, Mapping):
        return dict(obj)
    if is_dataclass(obj):
        try:
            return asdict(obj)
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        try:
            return dict(obj.__dict__)
        except Exception:
            return {}
    return {}


def _safe_float(x: Any) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _df_records(df: Any) -> List[Dict[str, Any]]:
    if not isinstance(df, pd.DataFrame) or df.empty:
        return []
    return df.to_dict(orient="records")


def _diag(code: str, message: str, *, missing: Optional[List[str]] = None, source: str) -> Dict[str, Any]:
    return {
        "code": str(code),
        "message": str(message),
        "missing": list(missing or []),
        "source": str(source),
    }


def _extract_graph(results_map: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
    graph = results_map.get("network_graph")
    if graph is None and isinstance(results_map.get("network_metrics"), Mapping):
        graph = results_map["network_metrics"].get("network_graph")
    if graph is None:
        return None
    if isinstance(graph, Mapping):
        return dict(graph)
    # Some typed models implement .to_dict()
    to_dict = getattr(graph, "to_dict", None)
    if callable(to_dict):
        try:
            val = to_dict()
            return dict(val) if isinstance(val, Mapping) else None
        except Exception:
            return None
    return None


def extract_stations_from_graph(graph: Mapping[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Strict extraction of station entities from a network graph.

    Expected schema:
      graph = {"nodes": [{"id": str, "type": "station", "lat": float, "lon": float}, ...], "edges": [...]}
    """

    diagnostics: List[Dict[str, Any]] = []
    nodes = graph.get("nodes")
    if not isinstance(nodes, list):
        diagnostics.append(
            _diag(
                "network_graph.nodes_missing",
                "network_graph missing required `nodes` list.",
                missing=["nodes"],
                source="network_graph",
            )
        )
        return [], diagnostics

    out: List[Dict[str, Any]] = []
    for i, node in enumerate(nodes):
        if not isinstance(node, Mapping):
            diagnostics.append(
                _diag(
                    "network_graph.node_invalid",
                    f"network_graph.nodes[{i}] is not an object.",
                    missing=["id", "type", "lat", "lon"],
                    source="network_graph",
                )
            )
            continue

        missing: List[str] = []
        node_id = node.get("id")
        node_type = node.get("type")
        lat = node.get("lat")
        lon = node.get("lon")

        if node_id is None:
            missing.append("id")
        if node_type is None:
            missing.append("type")
        if lat is None:
            missing.append("lat")
        if lon is None:
            missing.append("lon")

        if missing:
            diagnostics.append(
                _diag(
                    "network_graph.node_missing_fields",
                    f"network_graph.nodes[{i}] missing required fields.",
                    missing=missing,
                    source="network_graph",
                )
            )
            continue

        if str(node_type).lower() != "station":
            # Strict: we only project stations from station-typed nodes.
            continue

        lat_f = _safe_float(lat)
        lon_f = _safe_float(lon)
        if lat_f is None or lon_f is None:
            diagnostics.append(
                _diag(
                    "network_graph.node_invalid_coords",
                    f"network_graph.nodes[{i}] has non-numeric lat/lon.",
                    missing=["lat", "lon"],
                    source="network_graph",
                )
            )
            continue

        out.append({"id": str(node_id), "lat": lat_f, "lon": lon_f})

    if not out:
        diagnostics.append(
            _diag(
                "network_graph.no_station_nodes",
                "No station nodes extracted from network_graph.nodes (expected type == 'station' with lat/lon).",
                missing=["nodes[*].type=='station'", "nodes[*].lat", "nodes[*].lon"],
                source="network_graph",
            )
        )

    return out, diagnostics


def extract_links_from_graph(graph: Mapping[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Strict extraction of links from a network graph.

    Expected schema:
      graph = {"edges": [{"source": str, "target": str}, ...]}
    """

    diagnostics: List[Dict[str, Any]] = []
    edges = graph.get("edges")
    if not isinstance(edges, list):
        diagnostics.append(
            _diag(
                "network_graph.edges_missing",
                "network_graph missing required `edges` list.",
                missing=["edges"],
                source="network_graph",
            )
        )
        return [], diagnostics

    out: List[Dict[str, Any]] = []
    for i, edge in enumerate(edges):
        if not isinstance(edge, Mapping):
            diagnostics.append(
                _diag(
                    "network_graph.edge_invalid",
                    f"network_graph.edges[{i}] is not an object.",
                    missing=["source", "target"],
                    source="network_graph",
                )
            )
            continue

        missing: List[str] = []
        src = edge.get("source")
        dst = edge.get("target")
        if src is None:
            missing.append("source")
        if dst is None:
            missing.append("target")
        if missing:
            diagnostics.append(
                _diag(
                    "network_graph.edge_missing_fields",
                    f"network_graph.edges[{i}] missing required fields.",
                    missing=missing,
                    source="network_graph",
                )
            )
            continue

        out.append({"src": str(src), "dst": str(dst)})

    if not out:
        diagnostics.append(
            _diag(
                "network_graph.no_edges",
                "No links extracted from network_graph.edges.",
                missing=["edges[*].source", "edges[*].target"],
                source="network_graph",
            )
        )

    return out, diagnostics


def extract_coverage_points(results_map: Mapping[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Strict extraction of coverage points.

    Expected schema:
      results.coverage is a pandas DataFrame with columns: lat, lon, intensity
    """

    diagnostics: List[Dict[str, Any]] = []
    cov = results_map.get("coverage")
    if cov is None:
        diagnostics.append(
            _diag(
                "coverage.missing",
                "results missing required `coverage` DataFrame.",
                missing=["coverage"],
                source="coverage",
            )
        )
        return [], diagnostics

    if not isinstance(cov, pd.DataFrame):
        diagnostics.append(
            _diag(
                "coverage.invalid_type",
                f"results.coverage must be a pandas DataFrame, got {type(cov).__name__}.",
                missing=["DataFrame(lat, lon, intensity)"],
                source="coverage",
            )
        )
        return [], diagnostics

    if cov.empty:
        diagnostics.append(
            _diag(
                "coverage.empty",
                "results.coverage is an empty DataFrame.",
                missing=["rows"],
                source="coverage",
            )
        )
        return [], diagnostics

    required = ["lat", "lon", "intensity"]
    missing_cols = [c for c in required if c not in cov.columns]
    if missing_cols:
        diagnostics.append(
            _diag(
                "coverage.missing_columns",
                "results.coverage missing required columns.",
                missing=missing_cols,
                source="coverage",
            )
        )
        return [], diagnostics

    df = cov[required].copy()
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df["intensity"] = pd.to_numeric(df["intensity"], errors="coerce")
    df = df.dropna(subset=["lat", "lon", "intensity"])
    if df.empty:
        diagnostics.append(
            _diag(
                "coverage.no_valid_points",
                "results.coverage contains no valid numeric lat/lon/intensity points.",
                missing=["numeric lat/lon/intensity"],
                source="coverage",
            )
        )
        return [], diagnostics

    return _df_records(df), diagnostics


def extract_stations_from_spatial_observations(
    spatial_observations: Any,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Strict extraction of stations from a spatial observations frame.

    Expected schema:
      spatial_observations: DataFrame with columns station_id, station_lat, station_lon
    """

    diagnostics: List[Dict[str, Any]] = []
    if spatial_observations is None:
        diagnostics.append(
            _diag(
                "spatial_observations.missing",
                "results missing `spatial_observations`.",
                missing=["spatial_observations"],
                source="spatial_observations",
            )
        )
        return [], diagnostics

    if not isinstance(spatial_observations, pd.DataFrame):
        diagnostics.append(
            _diag(
                "spatial_observations.invalid_type",
                f"spatial_observations must be a pandas DataFrame, got {type(spatial_observations).__name__}.",
                missing=["DataFrame(station_id, station_lat, station_lon)"],
                source="spatial_observations",
            )
        )
        return [], diagnostics

    if spatial_observations.empty:
        diagnostics.append(
            _diag(
                "spatial_observations.empty",
                "spatial_observations is an empty DataFrame.",
                missing=["rows"],
                source="spatial_observations",
            )
        )
        return [], diagnostics

    required = ["station_id", "station_lat", "station_lon"]
    missing_cols = [c for c in required if c not in spatial_observations.columns]
    if missing_cols:
        diagnostics.append(
            _diag(
                "spatial_observations.missing_columns",
                "spatial_observations missing required columns.",
                missing=missing_cols,
                source="spatial_observations",
            )
        )
        return [], diagnostics

    df = spatial_observations[required].copy()
    df["station_id"] = df["station_id"].astype(str)
    df["lat"] = pd.to_numeric(df["station_lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["station_lon"], errors="coerce")
    df = df.dropna(subset=["lat", "lon"])
    if df.empty:
        diagnostics.append(
            _diag(
                "spatial_observations.no_valid_station_coords",
                "spatial_observations contains no valid numeric station_lat/station_lon rows.",
                missing=["numeric station_lat/station_lon"],
                source="spatial_observations",
            )
        )
        return [], diagnostics

    dedup = df.groupby("station_id", as_index=False).first()
    stations = [
        {"id": r["station_id"], "lat": float(r["lat"]), "lon": float(r["lon"])}
        for r in dedup.to_dict(orient="records")
    ]
    return stations, diagnostics


def extract_links_from_spatial_observations(
    spatial_observations: Any,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Strict extraction of station→aircraft links from spatial observations.

    Expected schema:
      spatial_observations: DataFrame with columns station_id, aircraft_id
    """

    diagnostics: List[Dict[str, Any]] = []
    if spatial_observations is None:
        diagnostics.append(
            _diag(
                "spatial_observations.missing",
                "results missing `spatial_observations`.",
                missing=["spatial_observations"],
                source="spatial_observations",
            )
        )
        return [], diagnostics

    if not isinstance(spatial_observations, pd.DataFrame):
        diagnostics.append(
            _diag(
                "spatial_observations.invalid_type",
                f"spatial_observations must be a pandas DataFrame, got {type(spatial_observations).__name__}.",
                missing=["DataFrame(station_id, aircraft_id)"],
                source="spatial_observations",
            )
        )
        return [], diagnostics

    if spatial_observations.empty:
        diagnostics.append(
            _diag(
                "spatial_observations.empty",
                "spatial_observations is an empty DataFrame.",
                missing=["rows"],
                source="spatial_observations",
            )
        )
        return [], diagnostics

    required = ["station_id", "aircraft_id"]
    missing_cols = [c for c in required if c not in spatial_observations.columns]
    if missing_cols:
        diagnostics.append(
            _diag(
                "spatial_observations.missing_columns",
                "spatial_observations missing required columns for link extraction.",
                missing=missing_cols,
                source="spatial_observations",
            )
        )
        return [], diagnostics

    pairs = spatial_observations[required].dropna().copy()
    if pairs.empty:
        diagnostics.append(
            _diag(
                "spatial_observations.no_links",
                "spatial_observations contains no station_id/aircraft_id pairs.",
                missing=["station_id", "aircraft_id"],
                source="spatial_observations",
            )
        )
        return [], diagnostics

    pairs["station_id"] = pairs["station_id"].astype(str)
    pairs["aircraft_id"] = pairs["aircraft_id"].astype(str)
    pairs = pairs.drop_duplicates()
    links = [{"src": r["station_id"], "dst": r["aircraft_id"]} for r in pairs.to_dict(orient="records")]
    return links, diagnostics


def build_spatial_entities(
    results: Any,
    *,
    strict: bool = True,
    allow_spatial_observations: bool = False,
) -> Dict[str, Any]:
    """Build spatial entities from existing analysis results.

    Constraints:
    - DO NOT recompute RF metrics or run models.
    - ONLY transform existing outputs already present on `results`.
    - Tolerate missing fields and return explicit diagnostics.

    Output format:
        {
          "stations": [{"id": "...", "lat": ..., "lon": ...}],
          "coverage": [{"lat": ..., "lon": ..., "intensity": ...}],
          "links": [{"src": "...", "dst": "..."}],
          "diagnostics": [...]
        }
    """

    results_map = _as_mapping(results)
    diagnostics: List[Dict[str, Any]] = []

    # ---- network_graph path (explicit, strict)
    graph = _extract_graph(results_map)
    if graph is None:
        diagnostics.append(
            _diag(
                "network_graph.missing",
                "results missing required `network_graph` for station/link extraction.",
                missing=["network_graph"],
                source="network_graph",
            )
        )
        stations: List[Dict[str, Any]] = []
        links: List[Dict[str, Any]] = []
        if strict:
            coverage, cov_diags = extract_coverage_points(results_map)
            diagnostics.extend(cov_diags)
            return {
                "stations": stations,
                "coverage": coverage,
                "links": links,
                "diagnostics": diagnostics,
            }
    else:
        stations, st_diags = extract_stations_from_graph(graph)
        links, lk_diags = extract_links_from_graph(graph)
        diagnostics.extend(st_diags)
        diagnostics.extend(lk_diags)

    # ---- coverage path (explicit schema only)
    coverage, cov_diags = extract_coverage_points(results_map)
    diagnostics.extend(cov_diags)

    # ---- optional explicit spatial_observations path (only if requested and not strict)
    if not strict and allow_spatial_observations:
        spatial = results_map.get("spatial_observations")
        if not stations:
            s_stations, s_diags = extract_stations_from_spatial_observations(spatial)
            stations = s_stations
            diagnostics.extend(s_diags)
        if not links:
            s_links, s_diags = extract_links_from_spatial_observations(spatial)
            links = s_links
            diagnostics.extend(s_diags)

    return {
        "stations": stations,
        "coverage": coverage,
        "links": links,
        "diagnostics": diagnostics,
    }


__all__ = [
    "build_spatial_entities",
    "extract_stations_from_graph",
    "extract_links_from_graph",
    "extract_coverage_points",
    "extract_stations_from_spatial_observations",
    "extract_links_from_spatial_observations",
]

