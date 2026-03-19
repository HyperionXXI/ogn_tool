from __future__ import annotations

import json
from typing import Any

from ogn_tool.reporting.ui_projection import build_ui_projection


def load_report_from_path(path: str) -> dict[str, Any] | None:
    if not path:
        return None
    try:
        with open(path, 'r', encoding='utf-8') as file_handle:
            return json.load(file_handle)
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

    projection = build_ui_projection(report)

    return {
        'network_summary': network_summary,
        'stations': station_health,
        'metrics': projection,
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
