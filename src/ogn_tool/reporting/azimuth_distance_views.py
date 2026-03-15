"""Projection layer for azimuth-distance analytical surfaces.

This module converts the azimuth-distance analytical primitive into
stable consumer-facing summaries without changing the meaning of matrix
cells.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def _azimuth_profile(azimuth_bins: list[float], matrix: np.ndarray, packet_count: int) -> list[dict[str, Any]]:
    counts = matrix.sum(axis=1, dtype=int) if matrix.size else np.zeros((0,), dtype=int)
    profile: list[dict[str, Any]] = []
    for idx, count in enumerate(counts.tolist()):
        profile.append(
            {
                'azimuth_start_deg': float(azimuth_bins[idx]),
                'azimuth_end_deg': float(azimuth_bins[idx + 1]),
                'count': int(count),
                'share': float(count / packet_count) if packet_count else 0.0,
            }
        )
    return profile


def _distance_profile(distance_bins_km: list[float], matrix: np.ndarray, packet_count: int) -> list[dict[str, Any]]:
    counts = matrix.sum(axis=0, dtype=int) if matrix.size else np.zeros((0,), dtype=int)
    profile: list[dict[str, Any]] = []
    for idx, count in enumerate(counts.tolist()):
        profile.append(
            {
                'distance_start_km': float(distance_bins_km[idx]),
                'distance_end_km': float(distance_bins_km[idx + 1]),
                'count': int(count),
                'share': float(count / packet_count) if packet_count else 0.0,
            }
        )
    return profile


def _build_rf_signature(
    azimuth_profile: list[dict[str, Any]],
    distance_profile: list[dict[str, Any]],
    packet_count: int,
) -> dict[str, Any] | None:
    if not azimuth_profile or not distance_profile:
        return None

    corridor_width_bins = min(3, len(azimuth_profile))
    shares = np.asarray([float(entry.get('share', 0.0)) for entry in azimuth_profile], dtype=float)
    if shares.size == 0 or corridor_width_bins <= 0:
        return None

    window_shares = np.asarray([
        shares[idx:idx + corridor_width_bins].sum()
        for idx in range(max(len(azimuth_profile) - corridor_width_bins + 1, 1))
    ], dtype=float)
    if window_shares.size == 0:
        return None

    dominant_idx = int(window_shares.argmax())
    dominant_share = float(window_shares[dominant_idx])
    dominant_corridor_start = float(azimuth_profile[dominant_idx]['azimuth_start_deg'])
    dominant_corridor_end = float(azimuth_profile[dominant_idx + corridor_width_bins - 1]['azimuth_end_deg'])
    corridor_width_deg = float(dominant_corridor_end - dominant_corridor_start)

    dominant_distance = max(distance_profile, key=lambda entry: int(entry.get('count', 0)))
    dominant_distance_band_share = float(dominant_distance.get('share', 0.0))
    nonzero_distance_band_count = int(sum(int(entry.get('count', 0)) > 0 for entry in distance_profile))
    distance_spread_index = (
        float(nonzero_distance_band_count / len(distance_profile))
        if distance_profile else 0.0
    )

    mean_share = float(shares.mean()) if shares.size else 0.0
    anisotropy_index = float(shares.max() / mean_share) if mean_share > 0 else 0.0

    return {
        'packet_count': int(packet_count),
        'dominant_corridor_start_deg': dominant_corridor_start,
        'dominant_corridor_end_deg': dominant_corridor_end,
        'corridor_width_deg': corridor_width_deg,
        'dominant_corridor_share': dominant_share,
        'dominant_distance_band_km': [
            float(dominant_distance['distance_start_km']),
            float(dominant_distance['distance_end_km']),
        ],
        'dominant_distance_band_share': dominant_distance_band_share,
        'nonzero_distance_band_count': nonzero_distance_band_count,
        'distance_spread_index': distance_spread_index,
        'anisotropy_index': anisotropy_index,
        'interpretation': 'directional traffic corridor likely',
    }


def _matrix_array(surface: dict[str, Any]) -> np.ndarray:
    matrix = np.asarray(surface.get('matrix', []), dtype=int)
    if matrix.ndim == 1 and matrix.size == 0:
        azimuth_bins = surface.get('azimuth_bins', []) or []
        distance_bins = surface.get('distance_bins_km', []) or []
        return np.zeros((max(len(azimuth_bins) - 1, 0), max(len(distance_bins) - 1, 0)), dtype=int)
    return matrix


def build_azimuth_distance_summary(surface: dict[str, Any]) -> dict[str, Any]:
    azimuth_bins = surface.get('azimuth_bins', []) or []
    distance_bins_km = surface.get('distance_bins_km', []) or []
    matrix = _matrix_array(surface)
    packet_count = int(surface.get('packet_count', int(matrix.sum())))

    nonzero_cells = int(np.count_nonzero(matrix))
    total_cells = int(matrix.size)
    max_cell_count = int(matrix.max()) if total_cells else 0
    azimuth_profile = _azimuth_profile(azimuth_bins, matrix, packet_count)
    distance_profile = _distance_profile(distance_bins_km, matrix, packet_count)

    dominant_cell = None
    if total_cells and max_cell_count > 0:
        az_idx, dist_idx = np.unravel_index(int(np.argmax(matrix)), matrix.shape)
        dominant_cell = {
            'azimuth_start_deg': float(azimuth_bins[az_idx]),
            'azimuth_end_deg': float(azimuth_bins[az_idx + 1]),
            'distance_start_km': float(distance_bins_km[dist_idx]),
            'distance_end_km': float(distance_bins_km[dist_idx + 1]),
            'count': max_cell_count,
        }

    rf_signature = _build_rf_signature(azimuth_profile, distance_profile, packet_count)

    return {
        'packet_count': packet_count,
        'azimuth_bin_count': max(len(azimuth_bins) - 1, 0),
        'distance_bin_count': max(len(distance_bins_km) - 1, 0),
        'nonzero_cell_count': nonzero_cells,
        'total_cell_count': total_cells,
        'max_cell_count': max_cell_count,
        'dominant_cell': dominant_cell,
        'azimuth_bins': azimuth_bins,
        'distance_bins_km': distance_bins_km,
        'azimuth_profile': azimuth_profile,
        'distance_profile': distance_profile,
        'rf_signature': rf_signature,
        'matrix': matrix.tolist(),
    }
