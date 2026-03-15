from __future__ import annotations

from typing import Any

from .directional_views import compute_dominant_arc, compute_top_sectors


def _azimuth_mid(sector: dict[str, Any]) -> float:
    return float(sector['start_deg'])


def build_directional_sectors(
    histogram: dict[str, Any],
    *,
    include_dominant_arc: bool = True,
) -> dict[str, Any]:
    edges = histogram.get('edges') or []
    hist = histogram.get('hist') or []
    packet_count = int(sum(hist)) if hist else 0

    sectors_by_weight: list[dict[str, Any]] = []
    sectors_by_azimuth: list[dict[str, Any]] = []
    if hist and edges and len(edges) == len(hist) + 1:
        sectors_by_weight = compute_top_sectors(edges, hist, packet_count, top_k=len(hist))
        sectors_by_azimuth = sorted(sectors_by_weight, key=_azimuth_mid)

    payload: dict[str, Any] = {
        'packet_count': packet_count,
        'sector_count': len(sectors_by_azimuth),
        'sectors_by_azimuth': sectors_by_azimuth,
        'sectors_by_weight': sectors_by_weight,
    }

    if include_dominant_arc:
        payload['dominant_arc'] = compute_dominant_arc(edges, hist, packet_count)

    return payload
