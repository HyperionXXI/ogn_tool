from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .run_comparison_views import compare_run_bundles
from .run_registry_views import get_registered_runs



def _load_report(bundle_path: str | Path) -> dict[str, Any]:
    bundle_dir = Path(bundle_path)
    report = json.loads((bundle_dir / 'report.json').read_text(encoding='utf-8'))
    return report if isinstance(report, dict) else {}



def _load_metadata(bundle_path: str | Path) -> dict[str, Any]:
    bundle_dir = Path(bundle_path)
    metadata = json.loads((bundle_dir / 'run_metadata.json').read_text(encoding='utf-8'))
    return metadata if isinstance(metadata, dict) else {}



def _build_lineage(run_entries: list[dict[str, Any]]) -> dict[str, Any]:
    if not run_entries:
        return {
            'consistent': True,
            'breakpoints': [],
            'reason': None,
        }

    breakpoints: list[dict[str, Any]] = []
    first = run_entries[0].get('comparability') if isinstance(run_entries[0].get('comparability'), dict) else {}
    baseline_analysis_version = first.get('analysis_version')
    baseline_config_identity = first.get('config_identity')

    for run in run_entries[1:]:
        comparability = run.get('comparability') if isinstance(run.get('comparability'), dict) else {}
        if comparability.get('analysis_version') != baseline_analysis_version:
            breakpoints.append({'run_id': run.get('run_id'), 'reason': 'analysis_version_changed'})
        if comparability.get('config_identity') != baseline_config_identity:
            breakpoints.append({'run_id': run.get('run_id'), 'reason': 'config_identity_changed'})

    return {
        'consistent': not breakpoints,
        'breakpoints': breakpoints,
        'reason': None if not breakpoints else 'metric lineage changed across selected runs',
    }



def _build_metrics_timeline(run_entries: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    redundancy_score: list[dict[str, Any]] = []
    critical_station_count: list[dict[str, Any]] = []
    confidence_score: list[dict[str, Any]] = []

    for run in run_entries:
        report = run.get('report') if isinstance(run.get('report'), dict) else {}
        network_risk = report.get('network_risk') if isinstance(report.get('network_risk'), dict) else {}
        network_status = report.get('network_status') if isinstance(report.get('network_status'), dict) else {}

        run_id = run.get('run_id')
        redundancy_score.append({'run': run_id, 'value': float(network_risk.get('redundancy_score') or 0.0)})
        critical_station_count.append({'run': run_id, 'value': int(network_status.get('critical_station_count') or 0)})
        confidence_score.append({'run': run_id, 'value': float(network_risk.get('confidence_score') or 0.0)})

    return {
        'redundancy_score': redundancy_score,
        'critical_station_count': critical_station_count,
        'confidence_score': confidence_score,
    }



def _extract_events(run_entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for previous, current in zip(run_entries, run_entries[1:]):
        comparison = compare_run_bundles(previous['path'], current['path'])
        topology_delta = comparison.get('topology_delta', {}) if isinstance(comparison.get('topology_delta'), dict) else {}
        summary_delta = comparison.get('summary_delta', {}) if isinstance(comparison.get('summary_delta'), dict) else {}

        for station_id in topology_delta.get('new_critical_stations', []):
            events.append({'run': current.get('run_id'), 'type': 'new_critical_station', 'station_id': station_id})

        redundancy_delta = summary_delta.get('redundancy_score', {}).get('delta')
        if redundancy_delta is None:
            prev_report = previous.get('report') if isinstance(previous.get('report'), dict) else {}
            curr_report = current.get('report') if isinstance(current.get('report'), dict) else {}
            prev_risk = prev_report.get('network_risk') if isinstance(prev_report.get('network_risk'), dict) else {}
            curr_risk = curr_report.get('network_risk') if isinstance(curr_report.get('network_risk'), dict) else {}
            prev_value = float(prev_risk.get('redundancy_score') or 0.0)
            curr_value = float(curr_risk.get('redundancy_score') or 0.0)
            redundancy_delta = curr_value - prev_value

        if redundancy_delta > 0:
            events.append({'run': current.get('run_id'), 'type': 'redundancy_improved', 'delta': redundancy_delta})
        elif redundancy_delta < 0:
            events.append({'run': current.get('run_id'), 'type': 'redundancy_declined', 'delta': redundancy_delta})

    return events



def _compute_trend(metrics_timeline: dict[str, list[dict[str, Any]]], lineage: dict[str, Any]) -> dict[str, str]:
    if not lineage.get('consistent'):
        return {
            'network_redundancy': 'unknown',
            'network_health': 'unknown',
        }

    redundancy_values = [point.get('value', 0.0) for point in metrics_timeline.get('redundancy_score', [])]
    critical_values = [point.get('value', 0.0) for point in metrics_timeline.get('critical_station_count', [])]

    redundancy_trend = 'stable'
    if len(redundancy_values) >= 2:
        if redundancy_values[-1] > redundancy_values[0]:
            redundancy_trend = 'improving'
        elif redundancy_values[-1] < redundancy_values[0]:
            redundancy_trend = 'declining'

    health_trend = 'stable'
    if len(critical_values) >= 2:
        if critical_values[-1] < critical_values[0]:
            health_trend = 'improving'
        elif critical_values[-1] > critical_values[0]:
            health_trend = 'declining'

    return {
        'network_redundancy': redundancy_trend,
        'network_health': health_trend,
    }



def compute_network_evolution(registry_dir: str | Path, last_n: int = 10) -> dict[str, Any]:
    """Compute stable historical evolution views for registered network analysis runs."""
    runs = get_registered_runs(Path(registry_dir))[:max(int(last_n), 0)]
    ordered_runs = list(reversed(runs))

    run_entries: list[dict[str, Any]] = []
    for run in ordered_runs:
        bundle_path = Path(run.get('path', ''))
        metadata = _load_metadata(bundle_path)
        comparability = metadata.get('comparability') if isinstance(metadata.get('comparability'), dict) else {}
        run_entries.append({
            'run_id': run.get('run_id'),
            'path': bundle_path,
            'report': _load_report(bundle_path),
            'metadata': metadata,
            'comparability': comparability,
        })

    lineage = _build_lineage(run_entries)
    metrics_timeline = _build_metrics_timeline(run_entries)
    events = _extract_events(run_entries) if lineage.get('consistent') else []
    trend = _compute_trend(metrics_timeline, lineage)

    return {
        'runs': [run.get('run_id') for run in run_entries],
        'lineage': lineage,
        'metrics_timeline': metrics_timeline,
        'events': events,
        'trend': trend,
    }


__all__ = ['compute_network_evolution']
