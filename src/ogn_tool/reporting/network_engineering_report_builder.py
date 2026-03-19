from __future__ import annotations

from typing import Any

import pandas as pd

from ogn_tool.intelligence.temporal.temporal_observability import (
    compute_temporal_observability,
)
from ogn_tool.reporting.views.network_metric_views import (
    network_confidence_level,
    network_redundancy_level,
    station_dependency_level,
)

from .network_engineering_report import NetworkEngineeringReport
from ogn_tool.reporting.report_views import temporal_observability_view

EXPECTED_DICT_METRICS = {
    'network_summary',
    'network_redundancy',
    'network_confidence',
}
EXPECTED_DATAFRAME_METRICS = {
    'station_health',
    'station_dependency',
    'station_dominance',
}


def _to_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if not isinstance(frame, pd.DataFrame) or frame.empty:
        return []
    return frame.to_dict(orient='records')


def build_network_report_contract(
    *,
    run_id: str,
    metadata: dict[str, Any],
    network_summary: dict[str, Any],
    station_health: pd.DataFrame,
    station_dependency: pd.DataFrame,
    network_robustness: dict[str, Any],
    station_placement: dict[str, Any],
    coverage_score: float | None,
) -> dict[str, Any]:
    """Build the canonical report JSON contract for reporting consumers."""
    return {
        'run_id': str(run_id),
        'metadata': dict(metadata),
        'network_metrics': {
            'network_summary': dict(network_summary),
            'station_health': _to_records(station_health),
            'station_dependency': _to_records(station_dependency),
            'network_robustness': dict(network_robustness),
            'station_placement': dict(station_placement),
        },
        'coverage_score': None if coverage_score is None else float(coverage_score),
    }


def _ensure_dict(metrics: dict[str, Any], key: str, warnings: list[str]) -> dict[str, Any]:
    value = metrics.get(key)
    if value is None:
        warnings.append(f'{key} missing from network_metrics')
        return {}
    if not isinstance(value, dict):
        warnings.append(f'{key} expected dict but got {type(value).__name__}')
        return {}
    return dict(value)


def _ensure_dataframe(metrics: dict[str, Any], key: str, warnings: list[str]) -> pd.DataFrame:
    value = metrics.get(key)
    if value is None:
        warnings.append(f'{key} missing from network_metrics')
        return pd.DataFrame()
    if not isinstance(value, pd.DataFrame):
        warnings.append(f'{key} expected DataFrame but got {type(value).__name__}')
        return pd.DataFrame()
    return value.copy()


def _ensure_spatial_observations(spatial_observations: Any, warnings: list[str]) -> pd.DataFrame:
    if spatial_observations is None:
        warnings.append('spatial_observations missing from reporting inputs')
        return pd.DataFrame()
    if not isinstance(spatial_observations, pd.DataFrame):
        warnings.append(f'spatial_observations expected DataFrame but got {type(spatial_observations).__name__}')
        return pd.DataFrame()
    return spatial_observations.copy()


def _collect_pipeline_warnings(metrics: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for key in ('_contract_warnings', '_coherence_warnings', '_confidence_warnings'):
        value = metrics.get(key, [])
        if isinstance(value, list):
            warnings.extend(str(item) for item in value)
    return warnings


def _collect_station_dependency_levels(metrics: dict[str, Any], station_dependency: pd.DataFrame) -> list[str]:
    if station_dependency.empty or 'station_id' not in station_dependency.columns:
        return []

    levels: list[str] = []
    for station_id in station_dependency['station_id'].dropna().astype(str).tolist():
        level = station_dependency_level(metrics, station_id)
        if level is not None:
            levels.append(level)
    return levels


def _build_recommended_actions(metrics: dict[str, Any], station_health: pd.DataFrame, station_dependency: pd.DataFrame) -> list[str]:
    actions: list[str] = []

    confidence_level = network_confidence_level(metrics)
    if confidence_level in {'weak', 'fair'}:
        actions.append('Collect more observations before making structural network decisions.')

    redundancy_level = network_redundancy_level(metrics)
    if redundancy_level in {'critical', 'fragile'}:
        actions.append('Prioritize redundancy improvements around single-station or weak-overlap areas.')

    if isinstance(station_health, pd.DataFrame) and not station_health.empty and 'health_status' in station_health.columns:
        critical = station_health[station_health['health_status'].astype(str) == 'CRITICAL']
        if not critical.empty:
            actions.append('Review CRITICAL stations first; they are currently the highest operational risk.')

    dependency_levels = _collect_station_dependency_levels(metrics, station_dependency)
    if 'critical' in dependency_levels:
        actions.append('Inspect critical station dependencies and validate overlap resilience.')
    elif 'elevated' in dependency_levels:
        actions.append('Review elevated station dependencies before changing network topology.')

    dominance = metrics.get('station_dominance')
    if isinstance(dominance, pd.DataFrame) and not dominance.empty and 'dominance_ratio' in dominance.columns:
        dominance_scores = pd.to_numeric(dominance['dominance_ratio'], errors='coerce').fillna(0.0)
        if bool((dominance_scores >= 0.7).any()):
            actions.append('Investigate stations with highly concentrated unique coverage.')

    deduped: list[str] = []
    for action in actions:
        if action not in deduped:
            deduped.append(action)
    return deduped


def build_network_engineering_report(
    metrics: dict[str, Any] | None,
    spatial_observations: pd.DataFrame | None,
) -> NetworkEngineeringReport:
    """Build the canonical network engineering report from existing analysis outputs.

    This builder only projects current metric surfaces and delegates
    qualitative interpretation to the canonical metric view layer.
    It does not compute or modify analysis metrics.
    """
    metrics = metrics if isinstance(metrics, dict) else {}
    warnings = _collect_pipeline_warnings(metrics)

    network_summary = _ensure_dict(metrics, 'network_summary', warnings)
    network_redundancy = _ensure_dict(metrics, 'network_redundancy', warnings)
    network_confidence = _ensure_dict(metrics, 'network_confidence', warnings)
    station_health = _ensure_dataframe(metrics, 'station_health', warnings)
    station_dependency = _ensure_dataframe(metrics, 'station_dependency', warnings)
    station_dominance = _ensure_dataframe(metrics, 'station_dominance', warnings)
    spatial_frame = _ensure_spatial_observations(spatial_observations, warnings)

    if spatial_frame is not None and not spatial_frame.empty and 'ts_epoch' in spatial_frame.columns:
        ts = spatial_frame['ts_epoch']
        window_hours = int((ts.max() - ts.min()) // 3600) + 1 if len(ts) > 0 else 0
        temporal = compute_temporal_observability(ts, window_hours)
        temporal_observability = temporal_observability_view(temporal)
    else:
        temporal_observability = {}

    analysis_stats = metrics.get('analysis_stats', {})
    report = NetworkEngineeringReport(
        network_summary=network_summary,
        station_health_table=station_health,
        network_redundancy=network_redundancy,
        network_confidence=network_confidence,
        station_dependency=station_dependency,
        station_dominance=station_dominance,
        spatial_observations=spatial_frame,
        recommended_actions=_build_recommended_actions(metrics, station_health, station_dependency),
        input_warnings=warnings,
        temporal_observability=temporal_observability,
        analysis_stats=analysis_stats,
    )
    return report


__all__ = ['build_network_engineering_report', 'build_network_report_contract']
