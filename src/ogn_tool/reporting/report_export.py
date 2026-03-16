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
    get_station_availability,
    get_analysis_confidence,
)

import subprocess


REPORT_EXPORT_VERSION = '1.0'
REPORT_SCHEMA_VERSION = '1.0'
RF_SIGNATURE_VERSION = 2
ANALYSIS_ENGINE_VERSION = '0.1'
METRIC_SCHEMA_VERSION = 1

def _git_info():
    try:
        commit = subprocess.check_output([
            "git", "rev-parse", "--short", "HEAD"
        ]).decode().strip()
        branch = subprocess.check_output([
            "git", "rev-parse", "--abbrev-ref", "HEAD"
        ]).decode().strip()
        dirty = bool(subprocess.check_output([
            "git", "status", "--porcelain"
        ]).decode().strip())
        return commit, branch, dirty
    except Exception:
        return "unknown", "unknown", None




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

    # Projections
    station_availability = get_station_availability(report)
    analysis_confidence = get_analysis_confidence(report)
    network_status = get_network_status(report)
    network_risk = get_network_risk_summary(report)

    commit, branch, dirty = _git_info()
    artifact = {
        'report_metadata': {
            'report_version': REPORT_EXPORT_VERSION,
            'report_schema_version': REPORT_SCHEMA_VERSION,
            'git_commit': commit,
            'git_branch': branch,
            'git_dirty': dirty,
            'generated_at': generated_at,
        },
        'metrics': {
            'station_availability': station_availability,
        },
        'diagnostics': {
            'analysis_confidence': analysis_confidence,
            'network_status': network_status,
            'network_risk': network_risk,
        },
        'rf_signature_version': RF_SIGNATURE_VERSION,
        'rf_signature': get_rf_signature(report),
        'recommended_actions': get_recommended_actions(report),
        # Backward compatibility: keep previous keys at root
        'station_availability': station_availability,
        'analysis_confidence': analysis_confidence,
        'network_status': network_status,
        'network_risk': network_risk,
        'station_health': get_station_health_summary(report),
    }
    if hasattr(report, 'analysis_stats') and report.analysis_stats:
        artifact['analysis_stats'] = report.analysis_stats
    return artifact


__all__ = [
    'REPORT_EXPORT_VERSION',
    'REPORT_SCHEMA_VERSION',
    'RF_SIGNATURE_VERSION',
    'export_network_report_json',
]
