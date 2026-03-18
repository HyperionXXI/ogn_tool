from __future__ import annotations

from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional

import pandas as pd


def _as_mapping(report: Any) -> Dict[str, Any]:
    if report is None:
        return {}
    if isinstance(report, Mapping):
        return dict(report)
    if is_dataclass(report):
        try:
            return asdict(report)
        except Exception:
            # fall through to __dict__
            pass
    if hasattr(report, "__dict__"):
        try:
            return dict(report.__dict__)
        except Exception:
            return {}
    return {}


def _df_to_records(value: Any) -> List[Dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, pd.DataFrame):
        if value.empty:
            return []
        return value.to_dict(orient="records")
    if isinstance(value, list):
        return [v for v in value if isinstance(v, dict)]
    return []


def _get(d: Mapping[str, Any], *path: str, default=None):
    cur: Any = d
    for key in path:
        if not isinstance(cur, Mapping) or key not in cur:
            return default
        cur = cur[key]
    return cur


def _iterable(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []


def _normalize_station(node: Mapping[str, Any]) -> Dict[str, Any]:
    station_id = node.get("station_id") or node.get("id") or node.get("name")
    lat = node.get("lat") or node.get("latitude")
    lon = node.get("lon") or node.get("longitude")
    out = dict(node)
    if station_id is not None:
        out["station_id"] = station_id
    if lat is not None:
        out["lat"] = lat
    if lon is not None:
        out["lon"] = lon
    return out


def _normalize_link(edge: Mapping[str, Any]) -> Dict[str, Any]:
    src = edge.get("source") or edge.get("from") or edge.get("src") or edge.get("station_id")
    dst = edge.get("target") or edge.get("to") or edge.get("dst") or edge.get("aircraft_id")
    out = dict(edge)
    if src is not None:
        out["source"] = src
    if dst is not None:
        out["target"] = dst
    return out


def build_ui_projection(report: Any) -> Dict[str, List[Dict[str, Any]]]:
    """Build a UI-oriented projection from a report-like object.

    Contract:
    - MUST NOT compute new RF metrics.
    - MUST only transform existing report data.
    - MUST be tolerant to missing fields and schema drift.

    Output:
        {
          "stations": [...],
          "links": [...],
          "coverage": [...],
          "blind_zones": [...],
          "risk_zones": [...]
        }
    """

    d = _as_mapping(report)

    # ---- Stations + links (prefer network_graph if present)
    network_graph = (
        _get(d, "network_metrics", "network_graph")
        or _get(d, "network_graph")
        or _get(d, "network_metrics", "graph")
        or {}
    )
    if not isinstance(network_graph, Mapping):
        network_graph = {}

    nodes = _iterable(network_graph.get("nodes"))
    edges = _iterable(network_graph.get("edges"))

    stations: List[Dict[str, Any]] = []
    links: List[Dict[str, Any]] = []

    if nodes:
        stations = [_normalize_station(n) for n in nodes if isinstance(n, Mapping)]

    if edges:
        links = [_normalize_link(e) for e in edges if isinstance(e, Mapping)]

    # Fallbacks: station_health_table often exists even when graph is absent
    if not stations:
        health = _get(d, "network_metrics", "station_health_table") or _get(d, "station_health_table")
        for row in _df_to_records(health):
            stations.append(
                _normalize_station(
                    {
                        "station_id": row.get("station_id") or row.get("id"),
                        "lat": row.get("lat") or row.get("station_lat"),
                        "lon": row.get("lon") or row.get("station_lon"),
                        "health_status": row.get("health_status"),
                        "impact_score": row.get("impact_score"),
                    }
                )
            )

    # ---- Coverage (probability field / grid)
    coverage_value = (
        _get(d, "coverage_metrics")
        or _get(d, "coverage")
        or _get(d, "rf_metrics", "coverage")
        or _get(d, "diagnostics", "coverage")
    )
    coverage = _df_to_records(coverage_value)

    # ---- Blind zones
    blind_value = (
        _get(d, "rf_metrics", "blind_zones")
        or _get(d, "blind_zones")
        or _get(d, "diagnostics", "blind_zones")
        or _get(d, "network_metrics", "blind_zones")
    )
    blind_zones = _df_to_records(blind_value)
    if not blind_zones and isinstance(blind_value, Mapping):
        # allow dict-based representations, e.g. {"features": [...]}
        features = blind_value.get("features")
        if isinstance(features, list):
            blind_zones = [f for f in features if isinstance(f, dict)]

    # ---- Risk zones (projection only: highlight already-classified risks)
    # Prefer explicit risk summaries/flags if present; otherwise derive from station health table.
    risk_zones: List[Dict[str, Any]] = []
    explicit_risks = _get(d, "risk_zones") or _get(d, "network_metrics", "risk_zones")
    risk_zones = _df_to_records(explicit_risks)

    if not risk_zones:
        health = _get(d, "network_metrics", "station_health_table") or _get(d, "station_health_table")
        for row in _df_to_records(health):
            status = str(row.get("health_status") or "").upper()
            if not status:
                continue
            if status not in {"CRITICAL", "WARNING"}:
                continue
            risk_zones.append(
                {
                    "type": "station",
                    "station_id": row.get("station_id") or row.get("id"),
                    "lat": row.get("lat") or row.get("station_lat"),
                    "lon": row.get("lon") or row.get("station_lon"),
                    "risk": status.lower(),
                    "impact_score": row.get("impact_score"),
                    "notes": row.get("notes"),
                }
            )

    return {
        "stations": stations,
        "links": links,
        "coverage": coverage,
        "blind_zones": blind_zones,
        "risk_zones": risk_zones,
    }


__all__ = ["build_ui_projection"]

