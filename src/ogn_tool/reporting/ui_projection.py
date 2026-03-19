from __future__ import annotations

from typing import Any, Dict, List, Mapping


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


def _normalize_station(row: Mapping[str, Any]) -> Dict[str, Any]:
    station_id = row.get('station_id')
    lat = _safe_float(row.get('lat'))
    lon = _safe_float(row.get('lon'))

    out: Dict[str, Any] = {'station_id': str(station_id) if station_id is not None else ''}
    if lat is not None:
        out['lat'] = lat
    if lon is not None:
        out['lon'] = lon
    if 'health_status' in row:
        out['health_status'] = row.get('health_status')
    if 'impact_score' in row:
        out['impact_score'] = row.get('impact_score')
    return out


def build_ui_projection(report: dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Build UI projection from canonical report contract only."""
    _require(isinstance(report, dict), 'report must be a dict')
    network_metrics = report.get('network_metrics')
    _require(isinstance(network_metrics, dict), 'report.network_metrics must be a dict')

    station_health = network_metrics.get('station_health')
    _require(isinstance(station_health, list), 'report.network_metrics.station_health must be a list')

    stations = [_normalize_station(row) for row in station_health if isinstance(row, Mapping)]

    risk_zones: List[Dict[str, Any]] = []
    for station in stations:
        status = str(station.get('health_status') or '').upper()
        if status not in {'CRITICAL', 'WARNING'}:
            continue
        lat = station.get('lat')
        lon = station.get('lon')
        if lat is None or lon is None:
            continue
        risk_zones.append(
            {
                'type': 'station',
                'station_id': station.get('station_id'),
                'lat': lat,
                'lon': lon,
                'risk': status.lower(),
                'impact_score': station.get('impact_score'),
            }
        )

    return {
        'stations': stations,
        'links': [],
        'coverage': [],
        'blind_zones': [],
        'risk_zones': risk_zones,
    }


__all__ = ['build_ui_projection']
