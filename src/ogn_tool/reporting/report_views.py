from __future__ import annotations

from typing import Any

import pandas as pd

from .network_engineering_report import NetworkEngineeringReport



def _as_report(report: Any) -> NetworkEngineeringReport:
    if not isinstance(report, NetworkEngineeringReport):
        raise TypeError('Expected NetworkEngineeringReport')
    return report



def get_network_status(report: NetworkEngineeringReport) -> dict[str, Any]:
    """Return the stable network status projection for external consumers."""
    report = _as_report(report)
    summary = report.network_summary if isinstance(report.network_summary, dict) else {}
    return {
        'network_status': summary.get('network_status', 'unknown'),
        'critical_station_count': int(summary.get('critical_station_count') or 0),
        'warning_station_count': int(summary.get('warning_station_count') or 0),
        'top_critical_station': summary.get('top_critical_station'),
        'notes': summary.get('notes', ''),
        'input_warnings': list(report.input_warnings),
    }



def get_station_health_summary(report: NetworkEngineeringReport) -> dict[str, Any]:
    """Return a compact summary of the station health table."""
    report = _as_report(report)
    table = report.station_health_table if isinstance(report.station_health_table, pd.DataFrame) else pd.DataFrame()

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



def get_network_risk_summary(report: NetworkEngineeringReport) -> dict[str, Any]:
    """Return the stable redundancy and confidence risk projection."""
    report = _as_report(report)
    redundancy = report.network_redundancy if isinstance(report.network_redundancy, dict) else {}
    confidence = report.network_confidence if isinstance(report.network_confidence, dict) else {}

    return {
        'redundancy_score': float(redundancy.get('redundancy_score') or 0.0),
        'redundancy_interpretation': str(redundancy.get('interpretation') or ''),
        'confidence_score': float(confidence.get('confidence_score') or 0.0),
        'risk_warnings': list(report.input_warnings),
    }



def get_rf_signature(report: NetworkEngineeringReport) -> dict[str, Any]:
    """Return the stable RF signature projection for external consumers."""
    report = _as_report(report)
    return dict(report.rf_signature) if isinstance(report.rf_signature, dict) else {}


def get_recommended_actions(report: NetworkEngineeringReport) -> list[str]:
    """Return a stable copy of the recommended actions section."""
    report = _as_report(report)
    return list(report.recommended_actions)


__all__ = [
    'get_network_status',
    'get_station_health_summary',
    'get_network_risk_summary',
    'get_rf_signature',
    'get_recommended_actions',
]
