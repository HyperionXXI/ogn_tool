from __future__ import annotations

from typing import Any


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _get_network_metrics(report: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(report, dict), 'report must be a dict')
    nm = report.get('network_metrics')
    _require(isinstance(nm, dict), 'report.network_metrics must be a dict')
    return nm


def build_diagnostics(report: dict[str, Any]) -> list[dict[str, Any]]:
    nm = _get_network_metrics(report)

    diagnostics: list[dict[str, Any]] = []

    robustness = nm.get('network_robustness', {})
    _require(isinstance(robustness, dict), 'network_robustness must be a dict')

    redundancy_score = float(robustness.get('redundancy_score') or 0.0)
    confidence = float(robustness.get('confidence_score') or 0.0)

    if redundancy_score < 0.5:
        diagnostics.append(
            {
                'type': 'network_fragility',
                'severity': 'warning',
                'message': 'Low network redundancy detected',
                'redundancy_score': redundancy_score,
                'confidence': confidence,
            }
        )

    if confidence < 0.5:
        diagnostics.append(
            {
                'type': 'low_confidence',
                'severity': 'warning',
                'message': 'Low confidence in analysis results',
                'confidence': confidence,
            }
        )

    return diagnostics


def build_alerts(report: dict[str, Any]) -> list[dict[str, Any]]:
    nm = _get_network_metrics(report)

    alerts: list[dict[str, Any]] = []

    health = nm.get('station_health', [])
    _require(isinstance(health, list), 'station_health must be a list')

    for station in health:
        if not isinstance(station, dict):
            continue

        status = str(station.get('health_status') or '').upper()
        station_id = station.get('station_id')

        if status == 'CRITICAL':
            alerts.append(
                {
                    'type': 'critical_station',
                    'severity': 'critical',
                    'station_id': station_id,
                }
            )
        elif status == 'WARNING':
            alerts.append(
                {
                    'type': 'degraded_station',
                    'severity': 'warning',
                    'station_id': station_id,
                }
            )

    return alerts


def build_recommendations(report: dict[str, Any]) -> list[dict[str, Any]]:
    nm = _get_network_metrics(report)

    recommendations: list[dict[str, Any]] = []

    robustness = nm.get('network_robustness', {})
    _require(isinstance(robustness, dict), 'network_robustness must be a dict')

    redundancy_score = float(robustness.get('redundancy_score') or 0.0)

    if redundancy_score < 0.4:
        recommendations.append(
            {
                'type': 'increase_redundancy',
                'priority': 'high',
                'message': 'Consider adding additional stations to improve redundancy',
            }
        )

    health = nm.get('station_health', [])
    _require(isinstance(health, list), 'station_health must be a list')
    critical_stations = [
        station
        for station in health
        if isinstance(station, dict) and str(station.get('health_status') or '').upper() == 'CRITICAL'
    ]

    if critical_stations:
        recommendations.append(
            {
                'type': 'fix_critical_stations',
                'priority': 'high',
                'count': len(critical_stations),
                'message': 'Immediate action required on critical stations',
            }
        )

    return recommendations


def build_report_intelligence(report: dict[str, Any]) -> dict[str, Any]:
    diagnostics = build_diagnostics(report)
    alerts = build_alerts(report)
    recommendations = build_recommendations(report)

    return {
        'diagnostics': diagnostics,
        'alerts': alerts,
        'recommended_actions': recommendations,
    }


__all__ = [
    'build_alerts',
    'build_diagnostics',
    'build_recommendations',
    'build_report_intelligence',
]
