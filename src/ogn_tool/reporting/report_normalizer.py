from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional


def _diag(code: str, message: str, *, path: str, expected: Optional[str] = None) -> Dict[str, Any]:
    d: Dict[str, Any] = {
        "code": str(code),
        "message": str(message),
        "path": str(path),
    }
    if expected is not None:
        d["expected"] = str(expected)
    return d



def _safe_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _extract_network_graph(report: Dict[str, Any], diagnostics: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Strict sources only
    root_graph = report.get("network_graph")
    nm = report.get("network_metrics")
    nm_graph = nm.get("network_graph") if isinstance(nm, dict) else None

    if root_graph is not None and nm_graph is not None:
        diagnostics.append(
            _diag(
                "network_graph_ambiguous_source",
                "network_graph is present both at report root and under network_metrics; root will be used.",
                path="network_graph",
                expected="single authoritative network_graph source",
            )
        )

    graph = root_graph if root_graph is not None else nm_graph

    if graph is None:
        diagnostics.append(
            _diag(
                "missing_network_graph",
                "Missing required network_graph section.",
                path="network_graph",
                expected="dict with nodes/edges",
            )
        )
        return {}

    if not isinstance(graph, dict):
        diagnostics.append(
            _diag(
                "invalid_network_graph_type",
                f"network_graph must be a dict, got {type(graph).__name__}.",
                path="network_graph",
                expected="dict with nodes/edges",
            )
        )
        return {}

    return dict(graph)


def _extract_nodes(graph: Dict[str, Any], diagnostics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    nodes = graph.get("nodes")
    if nodes is None:
        diagnostics.append(
            _diag(
                "missing_network_graph_nodes",
                "network_graph.nodes is missing.",
                path="network_graph.nodes",
                expected="list[dict]",
            )
        )
        return []
    if not isinstance(nodes, list):
        diagnostics.append(
            _diag(
                "invalid_network_graph_nodes_type",
                f"network_graph.nodes must be a list, got {type(nodes).__name__}.",
                path="network_graph.nodes",
                expected="list[dict]",
            )
        )
        return []
    return [dict(n) for n in nodes if isinstance(n, dict)]


def _extract_edges(graph: Dict[str, Any], diagnostics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    edges = graph.get("edges")
    if edges is None:
        diagnostics.append(
            _diag(
                "missing_network_graph_edges",
                "network_graph.edges is missing.",
                path="network_graph.edges",
                expected="list[dict]",
            )
        )
        return []
    if not isinstance(edges, list):
        diagnostics.append(
            _diag(
                "invalid_network_graph_edges_type",
                f"network_graph.edges must be a list, got {type(edges).__name__}.",
                path="network_graph.edges",
                expected="list[dict]",
            )
        )
        return []
    return [dict(e) for e in edges if isinstance(e, dict)]


def _build_station_layer(nodes: List[Dict[str, Any]], diagnostics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for idx, node in enumerate(nodes):
        if node.get("type") != "station":
            continue
        node_id = node.get("id")
        lat = _safe_float(node.get("lat"))
        lon = _safe_float(node.get("lon"))
        if node_id is None:
            diagnostics.append(
                _diag(
                    "station_missing_id",
                    "Station node missing id.",
                    path=f"network_graph.nodes[{idx}].id",
                    expected="string",
                )
            )
            continue
        if lat is None or lon is None:
            diagnostics.append(
                _diag(
                    "station_missing_coordinates",
                    "Station node missing coordinates (lat/lon).",
                    path=f"network_graph.nodes[{idx}]",
                    expected="{'id': str, 'lat': float, 'lon': float}",
                )
            )
            continue
        out.append({"id": str(node_id), "lat": lat, "lon": lon})
    return out


def _build_aircraft_layer(nodes: List[Dict[str, Any]], diagnostics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for idx, node in enumerate(nodes):
        if node.get("type") != "aircraft":
            continue
        node_id = node.get("id")
        lat = _safe_float(node.get("lat"))
        lon = _safe_float(node.get("lon"))
        altitude = _safe_float(node.get("altitude"))
        if node_id is None:
            diagnostics.append(
                _diag(
                    "aircraft_missing_id",
                    "Aircraft node missing id.",
                    path=f"network_graph.nodes[{idx}].id",
                    expected="string",
                )
            )
            continue
        if lat is None or lon is None:
            diagnostics.append(
                _diag(
                    "aircraft_missing_coordinates",
                    "Aircraft node missing coordinates (lat/lon).",
                    path=f"network_graph.nodes[{idx}]",
                    expected="{'id': str, 'lat': float, 'lon': float, 'altitude': float|null}",
                )
            )
            continue
        out.append({"id": str(node_id), "lat": lat, "lon": lon, "altitude": altitude})
    return out


def _build_coverage_layer(report: Dict[str, Any], diagnostics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    coverage = report.get("coverage")
    if coverage is None:
        diagnostics.append(
            _diag(
                "missing_coverage",
                "Missing required coverage section.",
                path="coverage",
                expected="list[{'lat': float, 'lon': float, 'intensity': float}]",
            )
        )
        return []
    if not isinstance(coverage, list):
        diagnostics.append(
            _diag(
                "invalid_coverage_type",
                f"coverage must be a list, got {type(coverage).__name__}.",
                path="coverage",
                expected="list[dict]",
            )
        )
        return []

    if len(coverage) == 0:
        diagnostics.append(
            _diag(
                "coverage_empty",
                "coverage is present but empty.",
                path="coverage",
                expected="non-empty list with numeric lat/lon/intensity",
            )
        )
        return []

    out: List[Dict[str, Any]] = []
    for idx, rec in enumerate(coverage):
        if not isinstance(rec, dict):
            diagnostics.append(
                _diag(
                    "invalid_coverage_record_type",
                    f"coverage[{idx}] must be a dict, got {type(rec).__name__}.",
                    path=f"coverage[{idx}]",
                    expected="dict",
                )
            )
            continue
        lat = _safe_float(rec.get("lat"))
        lon = _safe_float(rec.get("lon"))
        intensity = rec.get("intensity")
        if intensity is None:
            diagnostics.append(
                _diag(
                    "coverage_missing_intensity",
                    "Coverage record missing intensity.",
                    path=f"coverage[{idx}].intensity",
                    expected="float",
                )
            )
            continue
        intensity_f = _safe_float(intensity)
        if lat is None or lon is None or intensity_f is None:
            diagnostics.append(
                _diag(
                    "invalid_coverage_record",
                    "Coverage record must have numeric lat/lon/intensity.",
                    path=f"coverage[{idx}]",
                    expected="{'lat': float, 'lon': float, 'intensity': float}",
                )
            )
            continue
        out.append({"lat": lat, "lon": lon, "intensity": intensity_f})

    if not out:
        diagnostics.append(
            _diag(
                "coverage_all_invalid",
                "coverage is present but all records were rejected as invalid.",
                path="coverage",
                expected="non-empty list with numeric lat/lon/intensity",
            )
        )
    return out


def _build_edges_layer(edges: List[Dict[str, Any]], diagnostics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    allowed = {"reception", "coverage"}
    for idx, edge in enumerate(edges):
        source = edge.get("source")
        target = edge.get("target")
        edge_type = edge.get("type")
        if edge_type is None:
            edge_type = edge.get("relation")
        weight = edge.get("weight")

        if source is None or target is None:
            diagnostics.append(
                _diag(
                    "edge_missing_endpoints",
                    "Edge missing source/target.",
                    path=f"network_graph.edges[{idx}]",
                    expected="{'source': str, 'target': str, 'weight': float, 'type': str}",
                )
            )
            continue
        if edge_type not in allowed:
            diagnostics.append(
                _diag(
                    "edge_invalid_type",
                    "Edge type must be 'reception' or 'coverage'.",
                    path=f"network_graph.edges[{idx}].type",
                    expected="reception|coverage",
                )
            )
            continue
        weight_f = _safe_float(weight)
        if weight_f is None:
            diagnostics.append(
                _diag(
                    "edge_missing_weight",
                    "Edge weight missing or non-numeric.",
                    path=f"network_graph.edges[{idx}].weight",
                    expected="float",
                )
            )
            continue
        out.append({"source": str(source), "target": str(target), "weight": weight_f, "type": str(edge_type)})
    return out


def _extract_network_metrics(report: Dict[str, Any], diagnostics: List[Dict[str, Any]]) -> Dict[str, Any]:
    nm = report.get("network_metrics")
    if nm is None:
        diagnostics.append(
            _diag(
                "missing_network_metrics",
                "Missing required network_metrics section.",
                path="network_metrics",
                expected="dict",
            )
        )
        return {}
    if not isinstance(nm, dict):
        diagnostics.append(
            _diag(
                "invalid_network_metrics_type",
                f"network_metrics must be a dict, got {type(nm).__name__}.",
                path="network_metrics",
                expected="dict",
            )
        )
        return {}
    return dict(nm)


def _build_network_block(report: Dict[str, Any], diagnostics: List[Dict[str, Any]]) -> Dict[str, Any]:
    nm = _extract_network_metrics(report, diagnostics)

    summary = nm.get("network_summary")
    if not isinstance(summary, dict):
        diagnostics.append(
            _diag(
                "missing_network_summary",
                "Missing network_metrics.network_summary dict.",
                path="network_metrics.network_summary",
                expected="dict",
            )
        )
        summary = {}

    health = nm.get("station_health_table")
    if health is None:
        diagnostics.append(
            _diag(
                "missing_station_health_table",
                "Missing network_metrics.station_health_table.",
                path="network_metrics.station_health_table",
                expected="list[dict]",
            )
        )
        health_list: List[Dict[str, Any]] = []
    elif isinstance(health, list):
        health_list = [dict(r) for r in health if isinstance(r, dict)]
        if not health_list:
            diagnostics.append(
                _diag(
                    "station_health_table_empty",
                    "station_health_table is empty or invalid.",
                    path="network_metrics.station_health_table",
                    expected="non-empty list[dict]",
                )
            )
    else:
        diagnostics.append(
            _diag(
                "invalid_station_health_table_type",
                f"station_health_table must be a list[dict], got {type(health).__name__}.",
                path="network_metrics.station_health_table",
                expected="list[dict]",
            )
        )
        health_list = []

    dependency = nm.get("station_dependency")
    if dependency is None:
        diagnostics.append(
            _diag(
                "missing_station_dependency",
                "Missing network_metrics.station_dependency.",
                path="network_metrics.station_dependency",
                expected="list[dict]",
            )
        )
        dep_list: List[Dict[str, Any]] = []
    elif isinstance(dependency, list):
        dep_list = [dict(r) for r in dependency if isinstance(r, dict)]
        if not dep_list:
            diagnostics.append(
                _diag(
                    "station_dependency_empty",
                    "station_dependency is empty or invalid.",
                    path="network_metrics.station_dependency",
                    expected="non-empty list[dict]",
                )
            )
    else:
        diagnostics.append(
            _diag(
                "invalid_station_dependency_type",
                f"station_dependency must be a list[dict], got {type(dependency).__name__}.",
                path="network_metrics.station_dependency",
                expected="list[dict]",
            )
        )
        dep_list = []

    has_timeseries = bool(report.get("network_timeseries"))
    has_spatial = bool(report.get("spatial_observations"))
    confidence = {"has_timeseries": has_timeseries, "has_spatial": has_spatial}

    return {"summary": dict(summary), "health": health_list, "dependency": dep_list, "confidence": confidence}


def _extract_meta(metadata: Dict[str, Any], report: Dict[str, Any], diagnostics: List[Dict[str, Any]]) -> Dict[str, Any]:
    dataset = metadata.get("dataset") if isinstance(metadata.get("dataset"), dict) else {}
    comparability = metadata.get("comparability") if isinstance(metadata.get("comparability"), dict) else {}

    station_id = dataset.get("station_id")
    if station_id is None:
        diagnostics.append(
            _diag(
                "meta_missing_station_id",
                "metadata.dataset.station_id is missing.",
                path="metadata.dataset.station_id",
                expected="string",
            )
        )
        station_id = ""

    time_window = {
        "start": comparability.get("time_window_start"),
        "end": comparability.get("time_window_end"),
        "duration_s": comparability.get("time_window_duration_s"),
    }
    if time_window["start"] is None or time_window["end"] is None:
        diagnostics.append(
            _diag(
                "meta_missing_time_window",
                "metadata.comparability time window is missing.",
                path="metadata.comparability",
                expected="time_window_start/time_window_end",
            )
        )

    warnings = report.get("input_warnings")
    warnings_list = [str(w) for w in warnings] if isinstance(warnings, list) else []
    if not isinstance(warnings, list):
        diagnostics.append(
            _diag(
                "meta_missing_input_warnings",
                "report.input_warnings is missing or invalid.",
                path="report.input_warnings",
                expected="list[str]",
            )
        )

    confidence_score = None
    nm = report.get("network_metrics")
    if isinstance(nm, dict) and isinstance(nm.get("network_confidence"), dict):
        confidence_score = nm["network_confidence"].get("confidence_score")
    confidence_score_f = _safe_float(confidence_score)
    if confidence_score is None:
        diagnostics.append(
            _diag(
                "meta_missing_confidence_score",
                "network_metrics.network_confidence.confidence_score is missing.",
                path="network_metrics.network_confidence.confidence_score",
                expected="float",
            )
        )
    elif confidence_score_f is None:
        diagnostics.append(
            _diag(
                "meta_invalid_confidence_score",
                "confidence_score must be numeric.",
                path="network_metrics.network_confidence.confidence_score",
                expected="float",
            )
        )
    elif confidence_score_f < 0.0 or confidence_score_f > 1.0:
        diagnostics.append(
            _diag(
                "confidence_score_out_of_range",
                "confidence_score must be within [0, 1].",
                path="network_metrics.network_confidence.confidence_score",
                expected="float in [0, 1]",
            )
        )

    return {
        "station_id": str(station_id),
        "time_window": time_window,
        "data_quality": {"warnings": warnings_list, "confidence_score": confidence_score_f},
    }


def build_ui_artifact(report: dict, metadata: dict) -> dict:
    """Normalize report.json + run_metadata.json into a stable UI artifact.

    Constraints:
    - No kernel RF modifications (pure transformation)
    - No RF business logic / no recomputation
    - No silent inference / no heuristics
    - No pandas in output
    - Diagnostics are always returned
    """

    diagnostics: List[Dict[str, Any]] = []

    if not isinstance(report, dict):
        return {
            "meta": {"station_id": "", "time_window": {}, "data_quality": {"warnings": [], "confidence_score": None}},
            "layers": {"stations": [], "aircraft": [], "coverage": [], "edges": []},
            "network": {"summary": {}, "health": [], "dependency": []},
            "diagnostics": [
                _diag(
                    "invalid_report_type",
                    f"report must be a dict, got {type(report).__name__}.",
                    path="report",
                    expected="dict",
                )
            ],
        }

    if not isinstance(metadata, dict):
        diagnostics.append(
            _diag(
                "invalid_metadata_type",
                f"metadata must be a dict, got {type(metadata).__name__}.",
                path="metadata",
                expected="dict",
            )
        )
        metadata = {}

    report_dict = dict(report)
    metadata_dict = dict(metadata)

    graph = _extract_network_graph(report_dict, diagnostics)
    nodes = _extract_nodes(graph, diagnostics) if graph else []
    edges = _extract_edges(graph, diagnostics) if graph else []

    stations_layer = _build_station_layer(nodes, diagnostics)
    aircraft_layer = _build_aircraft_layer(nodes, diagnostics)
    edges_layer = _build_edges_layer(edges, diagnostics)
    coverage_layer = _build_coverage_layer(report_dict, diagnostics)

    network_block = _build_network_block(report_dict, diagnostics)

    # meta extraction (station_id/time_window/data_quality)
    meta_block = _extract_meta(metadata_dict, report_dict, diagnostics)

    return {
        "meta": meta_block,
        "layers": {
            "stations": stations_layer,
            "aircraft": aircraft_layer,
            "coverage": coverage_layer,
            "edges": edges_layer,
        },
        "network": {
            "summary": network_block.get("summary", {}),
            "health": network_block.get("health", []),
            "dependency": network_block.get("dependency", []),
            "confidence": network_block.get("confidence", {}),
        },
        "diagnostics": diagnostics,
    }


__all__ = ["build_ui_artifact"]

