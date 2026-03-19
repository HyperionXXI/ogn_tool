from __future__ import annotations

from typing import Any

from ogn_tool.models.spatial_view_model import SpatialView
from ogn_tool.reporting.spatial_views import build_spatial_view as _build_spatial_view


def temporal_observability_view(obs) -> dict:
    return {
        'window_hours': obs.window_hours,
        'hours_with_packets': obs.hours_with_packets,
        'temporal_coverage_ratio': obs.window_coverage_ratio,
        'packet_count': obs.packet_count,
        'packets_per_hour': obs.packets_per_hour,
        'median_gap_hours': obs.median_gap_hours,
        'max_gap_hours': obs.max_gap_hours,
        'largest_active_streak_hours': obs.largest_active_streak_hours,
        'data_gaps_detected': obs.data_gaps_detected,
        'activity_score': obs.activity_score,
    }


def _require_report(report: Any) -> dict[str, Any]:
    if not isinstance(report, dict):
        raise TypeError('Expected canonical report dict')
    network_metrics = report.get('network_metrics')
    if not isinstance(network_metrics, dict):
        raise TypeError('Expected canonical report dict')
    return report


def get_station_availability(report) -> dict:
    d = _require_report(report)
    metadata = d.get('metadata')
    if not isinstance(metadata, dict):
        return {}
    temporal = metadata.get('temporal_observability')
    return dict(temporal) if isinstance(temporal, dict) else {}


def get_analysis_confidence(report) -> dict:
    avail = get_station_availability(report)
    packet_volume_ok = avail.get('hours_with_packets', 0) >= 12
    temporal_coverage_ok = avail.get('temporal_coverage_ratio', 0) >= 0.2
    representative_window = packet_volume_ok and temporal_coverage_ok and not avail.get('data_gaps_detected', False)
    return {
        'packet_volume_ok': packet_volume_ok,
        'temporal_coverage_ok': temporal_coverage_ok,
        'representative_window': representative_window,
    }


def get_network_status(report) -> dict:
    d = _require_report(report)
    summary = d['network_metrics']['network_summary']
    return {
        'network_status': summary.get('network_status', 'unknown'),
        'critical_station_count': int(summary.get('critical_station_count') or 0),
        'warning_station_count': int(summary.get('warning_station_count') or 0),
        'top_critical_station': summary.get('top_critical_station'),
        'notes': summary.get('notes', ''),
    }


def get_station_health_summary(report) -> dict:
    d = _require_report(report)
    health = d['network_metrics']['station_health']
    if not isinstance(health, list) or not health:
        return {
            'station_count': 0,
            'critical_count': 0,
            'warning_count': 0,
            'good_count': 0,
            'critical_stations': [],
        }

    statuses = [str(item.get('health_status') or '') for item in health if isinstance(item, dict)]
    critical_stations = [
        str(item.get('station_id'))
        for item in health
        if isinstance(item, dict) and str(item.get('health_status') or '') == 'CRITICAL'
    ]
    return {
        'station_count': len(statuses),
        'critical_count': sum(1 for s in statuses if s == 'CRITICAL'),
        'warning_count': sum(1 for s in statuses if s == 'WARNING'),
        'good_count': sum(1 for s in statuses if s == 'GOOD'),
        'critical_stations': critical_stations,
    }


def get_network_risk_summary(report) -> dict:
    d = _require_report(report)
    robustness = d['network_metrics']['network_robustness']
    if not isinstance(robustness, dict):
        robustness = {}
    return {
        'redundancy_score': float(robustness.get('redundancy_score') or 0.0),
        'redundancy_interpretation': str(robustness.get('interpretation') or ''),
        'confidence_score': float(robustness.get('confidence_score') or 0.0),
        'risk_warnings': [],
    }


def get_rf_signature(report) -> dict:
    _require_report(report)
    return {}


def get_recommended_actions(report) -> list:
    _require_report(report)
    return []


def build_spatial_view(report_dict: dict) -> SpatialView:
    return _build_spatial_view(report_dict)


def build_report_view(report_dict: dict) -> dict:
    if not isinstance(report_dict, dict):
        return {'spatial': build_spatial_view(report_dict)}  # type: ignore[arg-type]
    return {**report_dict, 'spatial': build_spatial_view(report_dict)}


__all__ = [
    'get_network_status',
    'get_station_health_summary',
    'get_network_risk_summary',
    'get_rf_signature',
    'get_recommended_actions',
    'build_spatial_view',
    'build_report_view',
]
