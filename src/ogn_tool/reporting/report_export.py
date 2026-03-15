from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .network_engineering_report import NetworkEngineeringReport
from .report_views import (
    get_network_risk_summary,
    get_network_status,
    get_recommended_actions,
    get_rf_signature,
    get_station_health_summary,
)

REPORT_EXPORT_VERSION = '1.0'
REPORT_SCHEMA_VERSION = '1.0'
RF_SIGNATURE_VERSION = 2



def export_network_report_json(report: NetworkEngineeringReport) -> dict[str, Any]:
    """Export a stable JSON artifact from a NetworkEngineeringReport.

    Architectural rule:
    This module must consume report_views only and must not read internal
    fields from NetworkEngineeringReport.
    """
    if not isinstance(report, NetworkEngineeringReport):
        raise TypeError('Expected NetworkEngineeringReport')

    generated_at = (
        datetime.now(timezone.utc)
        .isoformat(timespec='seconds')
        .replace('+00:00', 'Z')
    )

    return {
        'report_metadata': {
            'report_version': REPORT_EXPORT_VERSION,
            'report_schema_version': REPORT_SCHEMA_VERSION,
            'generated_at': generated_at,
        },
        'network_status': get_network_status(report),
        'station_health': get_station_health_summary(report),
        'network_risk': get_network_risk_summary(report),
        'rf_signature_version': RF_SIGNATURE_VERSION,
        'rf_signature': get_rf_signature(report),
        'recommended_actions': get_recommended_actions(report),
    }


__all__ = ['REPORT_EXPORT_VERSION', 'REPORT_SCHEMA_VERSION', 'RF_SIGNATURE_VERSION', 'export_network_report_json']
