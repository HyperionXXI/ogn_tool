from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, cast

import pandas as pd

from ogn_tool.models.spatial_view_model import SpatialView
from ogn_tool.reporting.spatial_builder import (
    extract_coverage_points,
    extract_links_from_graph,
    extract_stations_from_graph,
)


def _diag(code: str, message: str, *, missing: Optional[List[str]] = None, source: str) -> Dict[str, Any]:
    return {
        "code": str(code),
        "message": str(message),
        "missing": list(missing or []),
        "source": str(source),
    }


def _get_network_graph(report: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
    graph = report.get("network_graph")
    if graph is None and isinstance(report.get("network_metrics"), Mapping):
        graph = report["network_metrics"].get("network_graph")
    return dict(graph) if isinstance(graph, Mapping) else None


def _build_coverage_dataframe(report: Mapping[str, Any]) -> Optional[pd.DataFrame]:
    """Convert a report coverage section to the strict DataFrame schema.

    Expected report schema (JSON-friendly):
      coverage: [{"lat": ..., "lon": ..., "intensity": ...}, ...]

    No heuristics: only these explicit keys are accepted.
    """

    coverage = report.get("coverage")
    if coverage is None:
        coverage = report.get("coverage_metrics")

    if coverage is None:
        return None

    if isinstance(coverage, list):
        # Strict: list items must be dicts; keys lat/lon/intensity must exist.
        rows = [r for r in coverage if isinstance(r, dict)]
        if not rows:
            return pd.DataFrame(columns=["lat", "lon", "intensity"])
        return pd.DataFrame(rows)

    return None


def build_spatial_view(report_dict: dict) -> SpatialView:
    """Bridge from report.json to strict spatial extraction helpers.

    - No RF computation
    - No DB access
    - No exceptions escape
    - Propagates diagnostics from spatial_builder
    - Adds top-level diagnostics when required sections are missing/invalid
    """

    empty: SpatialView = {"stations": [], "links": [], "coverage": [], "diagnostics": []}

    try:
        if not isinstance(report_dict, dict):
            return cast(
                SpatialView,
                {
                    **empty,
                    "diagnostics": [
                        _diag(
                            "spatial_view.invalid_report_type",
                            f"report_dict must be a dict, got {type(report_dict).__name__}.",
                            missing=["dict"],
                            source="report",
                        )
                    ],
                },
            )

        diagnostics: List[Dict[str, Any]] = []

        # ---- network_graph → stations + links
        graph = _get_network_graph(report_dict)
        if graph is None:
            diagnostics.append(
                _diag(
                    "spatial_view.network_graph_missing",
                    "report missing required network_graph section.",
                    missing=["network_graph"],
                    source="network_graph",
                )
            )
            graph = {}

        stations, st_diags = extract_stations_from_graph(graph)
        links, lk_diags = extract_links_from_graph(graph)
        diagnostics.extend(st_diags)
        diagnostics.extend(lk_diags)

        # ---- coverage → DataFrame(lat, lon, intensity) → coverage points
        cov_df = _build_coverage_dataframe(report_dict)
        if cov_df is None:
            diagnostics.append(
                _diag(
                    "spatial_view.coverage_missing",
                    "report missing required coverage section.",
                    missing=["coverage"],
                    source="coverage",
                )
            )
            cov_results_map = {"coverage": None}
        else:
            cov_results_map = {"coverage": cov_df}

        coverage, cov_diags = extract_coverage_points(cov_results_map)
        diagnostics.extend(cov_diags)

        return cast(
            SpatialView,
            {
                "stations": stations,
                "links": links,
                "coverage": coverage,
                "diagnostics": diagnostics,
            },
        )

    except Exception as e:
        # Non-throwing: return safe empty structure with a diagnostic
        return cast(
            SpatialView,
            {
                **empty,
                "diagnostics": [
                    _diag(
                        "spatial_view.exception",
                        f"Unhandled error while building spatial view: {e!r}",
                        missing=[],
                        source="report",
                    )
                ],
            },
        )


__all__ = ["build_spatial_view"]

