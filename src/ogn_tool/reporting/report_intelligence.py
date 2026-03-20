from __future__ import annotations

import math
from typing import Any


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _get_network_metrics(report: dict[str, Any]) -> dict[str, Any]:
    _require(isinstance(report, dict), 'report must be a dict')
    nm = report.get('network_metrics')
    _require(isinstance(nm, dict), 'report.network_metrics must be a dict')
    return nm


def _compute_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    dlon = math.radians(lon2 - lon1)
    lat1r = math.radians(lat1)
    lat2r = math.radians(lat2)

    x = math.sin(dlon) * math.cos(lat2r)
    y = math.cos(lat1r) * math.sin(lat2r) - math.sin(lat1r) * math.cos(lat2r) * math.cos(dlon)

    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360.0) % 360.0


def _uniformity_score(coverage: list[float]) -> float:
    mean = sum(coverage) / len(coverage)
    variance = sum((value - mean) ** 2 for value in coverage) / len(coverage)
    max_variance = (1.0 - (1.0 / len(coverage))) ** 2
    normalized = 1.0 - (variance / max_variance if max_variance > 0 else 0.0)
    return max(0.0, min(1.0, normalized))


def build_rf_signature(report: dict[str, Any]) -> dict[str, Any]:
    nm = _get_network_metrics(report)

    stations = nm.get('station_health', [])
    _require(isinstance(stations, list), 'station_health must be a list')

    coords: list[tuple[float, float]] = []
    for station in stations:
        if not isinstance(station, dict):
            continue
        lat = _safe_float(station.get('lat'))
        lon = _safe_float(station.get('lon'))
        if lat is None or lon is None:
            continue
        coords.append((lat, lon))

    if len(coords) < 3:
        return {}

    # NOTE: centroid approximation is acceptable here for small geographic areas.
    lat_mean = sum(lat for lat, _ in coords) / len(coords)
    lon_mean = sum(lon for _, lon in coords) / len(coords)

    bin_size = 30
    bins = [0] * (360 // bin_size)

    for lat, lon in coords:
        bearing = _compute_bearing(lat_mean, lon_mean, lat, lon)
        idx = int(bearing // bin_size) % len(bins)
        bins[idx] += 1

    total = sum(bins)
    if total == 0:
        return {}

    coverage = [count / total for count in bins]
    uniformity = _uniformity_score(coverage)

    top_bins = sorted(enumerate(coverage), key=lambda item: item[1], reverse=True)[:3]
    dominant = [idx * bin_size for idx, value in top_bins if value > 0]

    return {
        'azimuth_coverage': coverage,
        'dominant_directions': dominant,
        'coverage_uniformity_score': uniformity,
    }


def build_rf_directional_gaps(rf_signature: dict[str, Any]) -> dict[str, Any]:
    coverage = rf_signature.get('azimuth_coverage') if isinstance(rf_signature, dict) else None

    if not isinstance(coverage, list) or len(coverage) != 12:
        return {}

    mean = sum(coverage) / len(coverage)
    threshold = mean * 0.5

    gaps = [
        idx * 30
        for idx, value in enumerate(coverage)
        if _safe_float(value) is not None and float(value) < threshold
    ]

    if not gaps:
        return {}

    ratio = len(gaps) / len(coverage)

    if ratio > 0.5:
        severity = 'high'
    elif ratio > 0.25:
        severity = 'medium'
    else:
        severity = 'low'

    return {
        'gaps': gaps,
        'severity': severity,
    }




def build_rf_gap_structure(rf_gaps: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(rf_gaps, dict):
        return {}

    gaps = rf_gaps.get('gaps')
    if not isinstance(gaps, list) or not gaps:
        return {}

    normalized: list[int] = []
    for angle in gaps:
        numeric = _safe_float(angle)
        if numeric is None:
            continue
        int_angle = int(numeric) % 360
        normalized.append(int_angle)

    sorted_gaps = sorted(set(normalized))
    if not sorted_gaps:
        return {}

    clusters: list[list[int]] = []
    current_cluster = [sorted_gaps[0]]

    for angle in sorted_gaps[1:]:
        prev = current_cluster[-1]
        if (angle - prev) == 30:
            current_cluster.append(angle)
        else:
            clusters.append(current_cluster)
            current_cluster = [angle]

    clusters.append(current_cluster)

    if len(clusters) > 1:
        first = clusters[0]
        last = clusters[-1]
        if first[0] == 0 and last[-1] == 330:
            merged = last + first
            clusters = clusters[1:-1]
            clusters.insert(0, merged)

    def angular_distance(start: int, end: int) -> int:
        if end >= start:
            return end - start
        return (360 - start) + end

    structured: list[dict[str, int]] = []
    for cluster in clusters:
        start = cluster[0]
        end = cluster[-1]
        width = angular_distance(start, end) + 30
        structured.append({'start': start, 'end': end, 'width': width})

    largest_gap = max((cluster['width'] for cluster in structured), default=0)

    return {
        'clusters': structured,
        'largest_gap': largest_gap,
        'gap_count': len(structured),
    }


def build_rf_shadow_analysis(rf_signature: dict[str, Any], rf_gaps: dict[str, Any]) -> dict[str, Any]:
    if not rf_signature or not rf_gaps:
        return {}

    uniformity = _safe_float(rf_signature.get('coverage_uniformity_score'))
    gaps = rf_gaps.get('gaps') if isinstance(rf_gaps, dict) else None

    if uniformity is None or not isinstance(gaps, list) or not gaps:
        return {}

    suspected = uniformity < 0.5
    confidence = (1.0 - uniformity) * (len(gaps) / 12.0)
    confidence = max(0.0, min(1.0, confidence))

    if not suspected:
        return {}

    return {
        'suspected': True,
        'directions': gaps,
        'confidence': confidence,
    }

def build_diagnostics(report: dict[str, Any]) -> list[dict[str, Any]]:
    nm = _get_network_metrics(report)

    diagnostics: list[dict[str, Any]] = []

    robustness = nm.get('network_robustness', {})
    _require(isinstance(robustness, dict), 'network_robustness must be a dict')

    redundancy_score = _safe_float(robustness.get('redundancy_score')) or 0.0
    confidence = _safe_float(robustness.get('confidence_score')) or 0.0

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

    redundancy_score = _safe_float(robustness.get('redundancy_score')) or 0.0

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
    rf_signature = build_rf_signature(report)
    rf_gaps = build_rf_directional_gaps(rf_signature) if rf_signature else {}
    rf_gap_structure = build_rf_gap_structure(rf_gaps) if rf_gaps else {}
    rf_shadow = build_rf_shadow_analysis(rf_signature, rf_gaps)

    return {
        'diagnostics': diagnostics,
        'alerts': alerts,
        'recommended_actions': recommendations,
        'rf_analysis': {
            'rf_signature_version': 'v1',
            'rf_signature': rf_signature,
            'rf_directional_gaps': rf_gaps,
            'rf_gap_structure': rf_gap_structure,
            'rf_shadow_analysis': rf_shadow,
        },
    }


__all__ = [
    'build_alerts',
    'build_diagnostics',
    'build_recommendations',
    'build_report_intelligence',
    'build_rf_directional_gaps',
    'build_rf_gap_structure',
    'build_rf_shadow_analysis',
    'build_rf_signature',
]
