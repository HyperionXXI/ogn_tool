from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ogn_tool.reporting.report_intelligence import build_report_intelligence
from ogn_tool.reporting.spatial_network_builder import build_spatial_network_features
from ogn_tool.reporting.ui_projection import build_ui_projection


def _attach_local_artifacts(report: dict[str, Any], report_path: str) -> dict[str, Any]:
    path = Path(report_path)
    surface_path = path.parent / 'azimuth_distance_surface.json'
    if not surface_path.exists():
        return report

    try:
        with surface_path.open('r', encoding='utf-8') as file_handle:
            surface = json.load(file_handle)
    except Exception:
        return report

    if not isinstance(surface, dict):
        return report

    enriched = dict(report)
    artifacts = enriched.get('artifacts')
    artifacts_dict = dict(artifacts) if isinstance(artifacts, dict) else {}
    artifacts_dict['azimuth_distance_surface'] = surface
    enriched['artifacts'] = artifacts_dict
    return enriched


def load_report_from_path(path: str) -> dict[str, Any] | None:
    if not path:
        return None
    try:
        with open(path, 'r', encoding='utf-8') as file_handle:
            report = json.load(file_handle)
        if not isinstance(report, dict):
            return None
        return _attach_local_artifacts(report, path)
    except Exception:
        return None


def load_report_from_upload(upload) -> dict[str, Any] | None:
    if upload is None:
        return None
    try:
        return json.loads(upload.read().decode('utf-8'))
    except Exception:
        return None


def build_dashboard_payload(report: dict[str, Any]) -> dict[str, Any]:
    network_metrics = report['network_metrics']
    network_summary = dict(network_metrics['network_summary'])
    station_health = network_metrics['station_health']

    network_summary.setdefault('station_count', len(station_health))
    network_summary['coverage_score'] = report['coverage_score']

    intelligence = build_report_intelligence(report)
    projection = build_ui_projection(report, intelligence)

    aircraft_observations = report.get('aircraft_observations')
    if isinstance(aircraft_observations, list):
        projection['spatial_network_features'] = build_spatial_network_features(aircraft_observations)
    else:
        projection['spatial_network_features'] = build_spatial_network_features([])

    return {
        'network_summary': network_summary,
        'stations': station_health,
        'metrics': projection,
        'intelligence': intelligence,
        'debug': {
            'run_id': report['run_id'],
            'packet_count': network_summary.get('packet_count'),
        },
    }


__all__ = [
    'build_dashboard_payload',
    'load_report_from_path',
    'load_report_from_upload',
]
