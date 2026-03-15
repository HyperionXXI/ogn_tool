from __future__ import annotations

import json
from pathlib import Path
from typing import Any



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
    result['is_comparable'] = all(result.values())
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
    """Compare two exported run bundles using only stable artifact surfaces."""
    left_report, left_meta = _load_bundle(left_bundle)
    right_report, right_meta = _load_bundle(right_bundle)

    comparability = _compute_comparability(left_meta, right_meta)
    summary_delta = _compute_summary_delta(left_report, right_report)
    topology_delta = _compute_topology_delta(left_report, right_report)
    spatial_delta = _compute_spatial_delta(left_report, right_report)
    station_delta = _compute_station_delta(left_report, right_report)
    interpretation = _build_interpretation(comparability, summary_delta, topology_delta)

    return {
        'comparability': comparability,
        'summary_delta': summary_delta,
        'topology_delta': topology_delta,
        'spatial_delta': spatial_delta,
        'station_delta': station_delta,
        'interpretation': interpretation,
    }


__all__ = ['compare_run_bundles']
