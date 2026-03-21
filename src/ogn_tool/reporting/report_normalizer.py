from __future__ import annotations

from typing import Any, Dict

from ogn_tool.reporting.ui_projection import build_ui_projection


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _extract_meta(metadata: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    dataset = metadata.get('dataset')
    comparability = metadata.get('comparability')
    _require(isinstance(dataset, dict), 'metadata.dataset must be a dict')
    _require(isinstance(comparability, dict), 'metadata.comparability must be a dict')

    station_id = dataset.get('station_id')
    _require(isinstance(station_id, str) and station_id != '', 'metadata.dataset.station_id must be a non-empty string')

    time_window = {
        'start': comparability.get('time_window_start'),
        'end': comparability.get('time_window_end'),
        'duration_s': comparability.get('time_window_duration_s'),
    }

    network_metrics = report.get('network_metrics')
    _require(isinstance(network_metrics, dict), 'report.network_metrics must be a dict')
    summary = network_metrics.get('network_summary')
    _require(isinstance(summary, dict), 'report.network_metrics.network_summary must be a dict')

    confidence_score = summary.get('confidence_score')
    if confidence_score is None:
        confidence_score = summary.get('network_confidence_score')

    if confidence_score is not None:
        confidence_score = float(confidence_score)

    return {
        'station_id': station_id,
        'time_window': time_window,
        'data_quality': {
            'warnings': [],
            'confidence_score': confidence_score,
        },
    }


def build_ui_artifact(report: dict, metadata: dict) -> dict:
    """Build UI artifact from canonical report contract only."""
    _require(isinstance(report, dict), 'report must be a dict')
    _require(isinstance(metadata, dict), 'metadata must be a dict')

    network_metrics = report.get('network_metrics')
    _require(isinstance(network_metrics, dict), 'report.network_metrics must be a dict')

    summary = network_metrics.get('network_summary')
    health = network_metrics.get('station_health')
    dependency = network_metrics.get('station_dependency')
    _require(isinstance(summary, dict), 'report.network_metrics.network_summary must be a dict')
    _require(isinstance(health, list), 'report.network_metrics.station_health must be a list')
    _require(isinstance(dependency, list), 'report.network_metrics.station_dependency must be a list')

    return {
        'meta': _extract_meta(metadata, report),
        'layers': build_ui_projection(report),
        'network': {
            'summary': summary,
            'health': health,
            'dependency': dependency,
            'confidence': {},
        },
        'diagnostics': [],
    }


__all__ = ['build_ui_artifact']
