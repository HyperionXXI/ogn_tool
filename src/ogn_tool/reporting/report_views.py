from __future__ import annotations

def temporal_observability_view(obs) -> dict:
    """Vue structurée pour exposer toutes les métriques d'observabilité temporelle."""
    return {
        "window_hours": obs.window_hours,
        "hours_with_packets": obs.hours_with_packets,
        "temporal_coverage_ratio": obs.window_coverage_ratio,
        "packet_count": obs.packet_count,
        "packets_per_hour": obs.packets_per_hour,
        "median_gap_hours": obs.median_gap_hours,
        "max_gap_hours": obs.max_gap_hours,
        "largest_active_streak_hours": obs.largest_active_streak_hours,
        "data_gaps_detected": obs.data_gaps_detected,
        "activity_score": obs.activity_score,
    }

from typing import Any

import pandas as pd



def _as_dict(report):
    if hasattr(report, '__dict__'):
        return dict(report.__dict__)
    return dict(report)

def get_station_availability(report) -> dict:
    d = _as_dict(report)
    temporal = d.get('summary_metrics', {}).get('temporal_observability', {})
    if not temporal:
        temporal = d.get('temporal_observability', {})
    return dict(temporal) if isinstance(temporal, dict) else {}

def get_analysis_confidence(report) -> dict:
    avail = get_station_availability(report)
    packet_volume_ok = avail.get('hours_with_packets', 0) >= 12
    temporal_coverage_ok = avail.get('window_coverage_ratio', 0) >= 0.2
    representative_window = packet_volume_ok and temporal_coverage_ok and not avail.get('data_gaps_detected', False)
    return {
        'packet_volume_ok': packet_volume_ok,
        'temporal_coverage_ok': temporal_coverage_ok,
        'representative_window': representative_window,
    }

def get_network_status(report) -> dict:
    d = _as_dict(report)
    summary = d.get('network_metrics', {}).get('network_summary', {})
    if not summary:
        summary = d.get('network_summary', {})
    return {
        'network_status': summary.get('network_status', 'unknown'),
        'critical_station_count': int(summary.get('critical_station_count') or 0),
        'warning_station_count': int(summary.get('warning_station_count') or 0),
        'top_critical_station': summary.get('top_critical_station'),
        'notes': summary.get('notes', ''),
        'input_warnings': list(d.get('input_warnings', [])),
    }

def get_station_health_summary(report) -> dict:
    d = _as_dict(report)
    health = d.get('network_metrics', {}).get('station_health_table')
    if health is None:
        health = d.get('station_health_table')
    import pandas as pd
    table = health if isinstance(health, pd.DataFrame) else pd.DataFrame()
    if table.empty or 'health_status' not in table.columns:
        return {
            'station_count': 0,
            'critical_count': 0,
            'warning_count': 0,
            'good_count': 0,
            'critical_stations': [],
        }
    statuses = table['health_status'].astype(str)
    critical_rows = table[statuses == 'CRITICAL'] if 'station_id' in table.columns else pd.DataFrame()
    return {
        'station_count': int(len(table)),
        'critical_count': int((statuses == 'CRITICAL').sum()),
        'warning_count': int((statuses == 'WARNING').sum()),
        'good_count': int((statuses == 'GOOD').sum()),
        'critical_stations': critical_rows['station_id'].astype(str).tolist() if not critical_rows.empty else [],
    }

def get_network_risk_summary(report) -> dict:
    d = _as_dict(report)
    metrics = d.get('network_metrics', {})
    redundancy = metrics.get('network_redundancy', {})
    confidence = metrics.get('network_confidence', {})
    if not redundancy:
        redundancy = d.get('network_redundancy', {})
    if not confidence:
        confidence = d.get('network_confidence', {})
    return {
        'redundancy_score': float(redundancy.get('redundancy_score') or 0.0),
        'redundancy_interpretation': str(redundancy.get('interpretation') or ''),
        'confidence_score': float(confidence.get('confidence_score') or 0.0),
        'risk_warnings': list(d.get('input_warnings', [])),
    }

def get_rf_signature(report) -> dict:
    d = _as_dict(report)
    rf = d.get('rf_metrics', {})
    if not rf:
        rf = d.get('rf_signature', {})
    return dict(rf) if isinstance(rf, dict) else {}

def get_recommended_actions(report) -> list:
    d = _as_dict(report)
    actions = d.get('diagnostics', {}).get('recommended_actions')
    if actions is None:
        actions = d.get('recommended_actions', [])
    return list(actions) if isinstance(actions, (list, tuple)) else []


__all__ = [
    'get_network_status',
    'get_station_health_summary',
    'get_network_risk_summary',
    'get_rf_signature',
    'get_recommended_actions',
]
