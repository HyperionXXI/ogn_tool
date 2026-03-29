from __future__ import annotations

from typing import Any

from ogn_tool.ui.models.station_insight import (
    StationActivity,
    StationDirection,
    StationImpact,
    StationInsight,
    StationNetwork,
)


def _as_int(value: Any) -> int | None:
    try:
        if value is None:
            return None
        return int(value)
    except Exception:
        return None


def _as_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _as_str(value: Any) -> str:
    if value is None:
        return ''
    return str(value)


# NOTE:
# This adapter may derive lightweight indices from payload (e.g. graph adjacency)
# but MUST NOT compute new RF or network metrics.
def _build_covisibility_index(payload: dict[str, Any]) -> dict[str, list[str]]:
    metrics = payload.get('metrics', {}) if isinstance(payload, dict) else {}
    links = metrics.get('links', []) if isinstance(metrics, dict) else []

    index: dict[str, set[str]] = {}
    if not isinstance(links, list):
        return {}

    for edge in links:
        if not isinstance(edge, dict):
            continue
        source = _as_str(edge.get('source')).strip()
        target = _as_str(edge.get('target')).strip()
        if not source or not target:
            continue

        index.setdefault(source, set()).add(target)
        index.setdefault(target, set()).add(source)

    return {key: sorted(values) for key, values in index.items()}


def build_station_insights(payload: dict) -> list[StationInsight]:
    if not isinstance(payload, dict):
        return []

    stations = payload.get('stations', [])
    if not isinstance(stations, list):
        return []

    network_summary = payload.get('network_summary', {})
    if not isinstance(network_summary, dict):
        network_summary = {}

    intelligence = payload.get('intelligence', {})
    if not isinstance(intelligence, dict):
        intelligence = {}

    rf_analysis = intelligence.get('rf_analysis', {})
    if not isinstance(rf_analysis, dict):
        rf_analysis = {}

    rf_signature = rf_analysis.get('rf_signature', {})
    if not isinstance(rf_signature, dict):
        rf_signature = {}

    rf_gap_structure = rf_analysis.get('rf_gap_structure', {})
    if not isinstance(rf_gap_structure, dict):
        rf_gap_structure = {}

    covisibility_index = _build_covisibility_index(payload)

    station_count = _as_int(network_summary.get('station_count'))
    network_packet_count = _as_int(network_summary.get('packet_count'))
    reference_station_id = _as_str(payload.get('reference_station_id')).strip()

    result: list[StationInsight] = []
    for row in stations:
        if not isinstance(row, dict):
            continue

        station_id = _as_str(row.get('station_id')).strip()
        if not station_id:
            continue

        is_reference_station = bool(reference_station_id) and station_id == reference_station_id

        insight = StationInsight(
            station_id=station_id,
            health_status=_as_str(row.get('health_status')).upper(),
            activity=StationActivity(
                packet_count=_as_int(row.get('packet_count')) or network_packet_count,
                unique_aircraft=_as_int(row.get('unique_aircraft')),
            ),
            direction=StationDirection(
                corridor_center_deg=(
                    _as_float(rf_signature.get('corridor_center_deg')) if is_reference_station else None
                ),
                dominant_corridor_share=(
                    _as_float(rf_signature.get('dominant_corridor_share')) if is_reference_station else None
                ),
                coverage_uniformity_score=(
                    _as_float(rf_signature.get('coverage_uniformity_score')) if is_reference_station else None
                ),
                gap_count=(
                    _as_int(rf_gap_structure.get('gap_count')) if is_reference_station else None
                ),
                largest_gap_deg=(
                    _as_float(rf_gap_structure.get('largest_gap')) if is_reference_station else None
                ),
            ),
            network=StationNetwork(
                station_count=station_count,
                co_visible_stations=covisibility_index.get(station_id, []),
            ),
            impact=StationImpact(
                impact_score=_as_float(row.get('impact_score')),
                only_seen_aircraft_count=None,
            ),
        )
        result.append(insight)

    return result


__all__ = ['build_station_insights']
