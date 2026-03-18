from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Tuple

from ogn_tool.reporting import report_views


def _diag(code: str, message: str, *, source: str, missing: Optional[List[str]] = None) -> Dict[str, Any]:
    return {
        "code": str(code),
        "message": str(message),
        "missing": list(missing or []),
        "source": str(source),
    }


def _as_report_dict(report: Any, *, label: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    if isinstance(report, dict):
        return dict(report), []
    if isinstance(report, Mapping):
        return dict(report), []
    return (
        {},
        [
            _diag(
                "comparison.invalid_report_type",
                f"{label} must be dict-like, got {type(report).__name__}.",
                source="report",
                missing=["dict"],
            )
        ],
    )


def _safe_call(fn, arg, *, code: str, source: str, default):
    try:
        return fn(arg), []
    except Exception as e:
        return default, [_diag(code, f"{fn.__name__} failed: {e!r}", source=source)]


def _spatial_counts(spatial: dict) -> Dict[str, int]:
    stations = spatial.get("stations") if isinstance(spatial.get("stations"), list) else []
    links = spatial.get("links") if isinstance(spatial.get("links"), list) else []
    coverage = spatial.get("coverage") if isinstance(spatial.get("coverage"), list) else []
    return {
        "stations": int(len(stations)),
        "links": int(len(links)),
        "coverage": int(len(coverage)),
    }


def _has_spatial_section(report: Dict[str, Any], key: str) -> bool:
    val = report.get(key)
    return isinstance(val, (list, dict))


def _numeric(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool):
        return float(int(value))
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _delta(a: Any, b: Any) -> Dict[str, Any]:
    a_num = _numeric(a)
    b_num = _numeric(b)
    delta_val = None
    if a_num is not None and b_num is not None:
        delta_val = b_num - a_num
    return {"a": a_num if a_num is not None else a, "b": b_num if b_num is not None else b, "delta": delta_val}


def _get_network_metrics(report: Dict[str, Any]) -> Dict[str, Any]:
    nm = report.get("network_metrics")
    return nm if isinstance(nm, dict) else {}


def _get_network_summary(report: Dict[str, Any]) -> Dict[str, Any]:
    nm = _get_network_metrics(report)
    ns = nm.get("network_summary")
    return ns if isinstance(ns, dict) else {}


def _get_summary_metrics(report: Dict[str, Any]) -> Dict[str, Any]:
    sm = report.get("summary_metrics")
    return sm if isinstance(sm, dict) else {}


def build_run_comparison_view(report_a: dict, report_b: dict) -> dict:
    """Build a stable comparison view between two reports.

    Rules:
    - Never raises
    - Uses only `report_views` outputs (no RF engine, no DB, no pipeline)
    - Does not mutate inputs
    - Always returns diagnostics
    """

    diagnostics: List[Dict[str, Any]] = []

    a, diags_a = _as_report_dict(report_a, label="report_a")
    b, diags_b = _as_report_dict(report_b, label="report_b")
    diagnostics.extend(diags_a)
    diagnostics.extend(diags_b)

    spatial_a, d1 = _safe_call(
        report_views.build_spatial_view,
        a,
        code="comparison.spatial_view_failed",
        source="spatial",
        default={"stations": [], "links": [], "coverage": [], "diagnostics": []},
    )
    spatial_b, d2 = _safe_call(
        report_views.build_spatial_view,
        b,
        code="comparison.spatial_view_failed",
        source="spatial",
        default={"stations": [], "links": [], "coverage": [], "diagnostics": []},
    )
    diagnostics.extend(d1)
    diagnostics.extend(d2)

    counts_a = _spatial_counts(spatial_a)
    counts_b = _spatial_counts(spatial_b)

    # Comparability flags are intentionally schema-based and non-interpreting.
    network_metrics_a = _get_network_metrics(a)
    network_metrics_b = _get_network_metrics(b)
    summary_metrics_a = _get_summary_metrics(a)
    summary_metrics_b = _get_summary_metrics(b)

    has_graph_a = bool(a.get("network_graph") or network_metrics_a.get("network_graph"))
    has_graph_b = bool(b.get("network_graph") or network_metrics_b.get("network_graph"))
    has_cov_a = _has_spatial_section(a, "coverage") or _has_spatial_section(a, "coverage_metrics")
    has_cov_b = _has_spatial_section(b, "coverage") or _has_spatial_section(b, "coverage_metrics")

    if not isinstance(a.get("network_metrics"), dict):
        diagnostics.append(
            _diag(
                "comparison.missing_network_metrics",
                "report_a missing `network_metrics` dict.",
                source="network_metrics",
                missing=["network_metrics"],
            )
        )
    if not isinstance(b.get("network_metrics"), dict):
        diagnostics.append(
            _diag(
                "comparison.missing_network_metrics",
                "report_b missing `network_metrics` dict.",
                source="network_metrics",
                missing=["network_metrics"],
            )
        )
    if not isinstance(a.get("summary_metrics"), dict):
        diagnostics.append(
            _diag(
                "comparison.missing_summary_metrics",
                "report_a missing `summary_metrics` dict.",
                source="summary_metrics",
                missing=["summary_metrics"],
            )
        )
    if not isinstance(b.get("summary_metrics"), dict):
        diagnostics.append(
            _diag(
                "comparison.missing_summary_metrics",
                "report_b missing `summary_metrics` dict.",
                source="summary_metrics",
                missing=["summary_metrics"],
            )
        )

    comparability = {
        "spatial": {
            "has_network_graph_a": bool(has_graph_a),
            "has_network_graph_b": bool(has_graph_b),
            "has_coverage_a": bool(has_cov_a),
            "has_coverage_b": bool(has_cov_b),
            "comparable": bool(has_graph_a and has_graph_b and has_cov_a and has_cov_b),
        },
        "summary": {
            "has_summary_metrics_a": isinstance(a.get("summary_metrics"), dict),
            "has_summary_metrics_b": isinstance(b.get("summary_metrics"), dict),
            "comparable": bool(isinstance(a.get("summary_metrics"), dict) and isinstance(b.get("summary_metrics"), dict)),
        },
        "topology": {
            "comparable": bool(has_graph_a and has_graph_b),
        },
    }

    # Summary delta: only deltas over existing report fields (no interpretation)
    network_summary_a = _get_network_summary(a)
    network_summary_b = _get_network_summary(b)
    if not network_summary_a:
        diagnostics.append(
            _diag(
                "comparison.missing_network_summary",
                "report_a missing `network_metrics.network_summary` dict.",
                source="network_metrics",
                missing=["network_metrics.network_summary"],
            )
        )
    if not network_summary_b:
        diagnostics.append(
            _diag(
                "comparison.missing_network_summary",
                "report_b missing `network_metrics.network_summary` dict.",
                source="network_metrics",
                missing=["network_metrics.network_summary"],
            )
        )

    summary_delta = {
        "critical_station_count": _delta(
            network_summary_a.get("critical_station_count"), network_summary_b.get("critical_station_count")
        ),
        "warning_station_count": _delta(
            network_summary_a.get("warning_station_count"), network_summary_b.get("warning_station_count")
        ),
        "network_status": {
            "a": network_summary_a.get("network_status"),
            "b": network_summary_b.get("network_status"),
            "changed": network_summary_a.get("network_status") != network_summary_b.get("network_status"),
        },
    }

    # Topology delta: count-level deltas based on spatial view (graph-derived when present)
    topology_delta = {
        "station_count": _delta(counts_a["stations"], counts_b["stations"]),
        "link_count": _delta(counts_a["links"], counts_b["links"]),
    }

    # Spatial delta: count-level deltas (UI-relevant)
    spatial_delta = {
        "station_count": _delta(counts_a["stations"], counts_b["stations"]),
        "link_count": _delta(counts_a["links"], counts_b["links"]),
        "coverage_point_count": _delta(counts_a["coverage"], counts_b["coverage"]),
        "counts": {"a": counts_a, "b": counts_b},
    }

    return {
        "comparability": comparability,
        "summary_delta": summary_delta,
        "topology_delta": topology_delta,
        "spatial_delta": spatial_delta,
        "diagnostics": diagnostics,
    }






def _load_bundle(bundle_path: str | Path) -> tuple[dict[str, Any], dict[str, Any]]:
    bundle_dir = Path(bundle_path)
    report = json.loads((bundle_dir / 'report.json').read_text(encoding='utf-8'))
    metadata = json.loads((bundle_dir / 'run_metadata.json').read_text(encoding='utf-8'))
    return report if isinstance(report, dict) else {}, metadata if isinstance(metadata, dict) else {}



def _build_metric_delta(left_value: Any, right_value: Any) -> dict[str, Any]:
    left_num = float(left_value or 0.0)
    right_num = float(right_value or 0.0)
    return {
        'left': left_num,
        'right': right_num,
        'delta': right_num - left_num,
    }



def _compute_comparability(left_meta: dict[str, Any], right_meta: dict[str, Any]) -> dict[str, Any]:
    left_dataset = left_meta.get('dataset') if isinstance(left_meta.get('dataset'), dict) else {}
    right_dataset = right_meta.get('dataset') if isinstance(right_meta.get('dataset'), dict) else {}
    left_comp = left_meta.get('comparability') if isinstance(left_meta.get('comparability'), dict) else {}
    right_comp = right_meta.get('comparability') if isinstance(right_meta.get('comparability'), dict) else {}

    result = {
        'dataset_identity_match': bool(left_dataset) and bool(right_dataset) and left_dataset.get('dataset_id') == right_dataset.get('dataset_id'),
        'analysis_version_match': bool(left_comp) and bool(right_comp) and left_comp.get('analysis_version') == right_comp.get('analysis_version'),
        'config_identity_match': bool(left_comp) and bool(right_comp) and left_comp.get('config_identity') == right_comp.get('config_identity'),
        'time_window_duration_match': bool(left_comp) and bool(right_comp) and left_comp.get('time_window_duration_s') == right_comp.get('time_window_duration_s'),
    }
    result['is_comparable'] = bool(result['analysis_version_match'] and result['config_identity_match'] and result['time_window_duration_match'])
    return result



def _compute_summary_delta(left_report: dict[str, Any], right_report: dict[str, Any]) -> dict[str, Any]:
    left_network = left_report.get('network_status') if isinstance(left_report.get('network_status'), dict) else {}
    right_network = right_report.get('network_status') if isinstance(right_report.get('network_status'), dict) else {}
    left_station_health = left_report.get('station_health') if isinstance(left_report.get('station_health'), dict) else {}
    right_station_health = right_report.get('station_health') if isinstance(right_report.get('station_health'), dict) else {}
    left_risk = left_report.get('network_risk') if isinstance(left_report.get('network_risk'), dict) else {}
    right_risk = right_report.get('network_risk') if isinstance(right_report.get('network_risk'), dict) else {}

    return {
        'station_count': _build_metric_delta(left_station_health.get('station_count'), right_station_health.get('station_count')),
        'critical_station_count': _build_metric_delta(left_network.get('critical_station_count'), right_network.get('critical_station_count')),
        'warning_station_count': _build_metric_delta(left_network.get('warning_station_count'), right_network.get('warning_station_count')),
        'redundancy_score': _build_metric_delta(left_risk.get('redundancy_score'), right_risk.get('redundancy_score')),
        'confidence_score': _build_metric_delta(left_risk.get('confidence_score'), right_risk.get('confidence_score')),
    }



def _compute_topology_delta(left_report: dict[str, Any], right_report: dict[str, Any]) -> dict[str, Any]:
    left_station_health = left_report.get('station_health') if isinstance(left_report.get('station_health'), dict) else {}
    right_station_health = right_report.get('station_health') if isinstance(right_report.get('station_health'), dict) else {}
    left_critical = {str(station_id) for station_id in left_station_health.get('critical_stations', [])}
    right_critical = {str(station_id) for station_id in right_station_health.get('critical_stations', [])}

    return {
        'new_critical_stations': sorted(right_critical - left_critical),
        'resolved_critical_stations': sorted(left_critical - right_critical),
    }



def _compute_spatial_delta(left_report: dict[str, Any], right_report: dict[str, Any]) -> dict[str, Any]:
    _ = left_report, right_report
    return {}



def _compute_station_delta(left_report: dict[str, Any], right_report: dict[str, Any]) -> dict[str, Any]:
    _ = left_report, right_report
    return {}



def _build_interpretation(comparability: dict[str, Any], summary_delta: dict[str, Any], topology_delta: dict[str, Any]) -> dict[str, Any]:
    if not comparability.get('is_comparable'):
        return {
            'network_trend': 'not_comparable',
            'main_changes': ['Runs are not comparable under current metadata guards.'],
        }

    main_changes: list[str] = []
    redundancy_delta = summary_delta.get('redundancy_score', {}).get('delta', 0.0)
    critical_delta = summary_delta.get('critical_station_count', {}).get('delta', 0.0)

    if redundancy_delta > 0:
        main_changes.append('Network redundancy improved.')
    elif redundancy_delta < 0:
        main_changes.append('Network redundancy declined.')

    if critical_delta > 0:
        main_changes.append('More critical stations are present in the newer run.')
    elif critical_delta < 0:
        main_changes.append('Fewer critical stations are present in the newer run.')

    if topology_delta.get('new_critical_stations'):
        main_changes.append('New critical stations appeared.')
    if topology_delta.get('resolved_critical_stations'):
        main_changes.append('Some previously critical stations were resolved.')

    if redundancy_delta > 0 and critical_delta <= 0:
        network_trend = 'improving'
    elif redundancy_delta < 0 or critical_delta > 0:
        network_trend = 'degrading'
    else:
        network_trend = 'stable'

    return {
        'network_trend': network_trend,
        'main_changes': main_changes,
    }



def compare_run_bundles(left_bundle: str | Path, right_bundle: str | Path) -> dict[str, Any]:
    """Compare two exported run bundles using only stable artifact surfaces.

    This function delegates delta computations to the same logic as
    `build_run_comparison_view` to prevent divergence.
    """

    left_report, left_meta = _load_bundle(left_bundle)
    right_report, right_meta = _load_bundle(right_bundle)

    view = build_run_comparison_view(left_report, right_report)

    # Preserve metadata comparability flags from bundle metadata (non-RF).
    view["comparability"] = {
        **view.get("comparability", {}),
        "bundle": _compute_comparability(left_meta, right_meta),
    }

    # Keep output schema stable; avoid interpretation here (projection-only).
    view.setdefault("station_delta", {})
    view.setdefault("interpretation", {})
    return view


__all__ = ["build_run_comparison_view", "compare_run_bundles"]
