"""Projection layer for azimuth-distance analytical surfaces.

This module converts the azimuth-distance analytical primitive into
stable consumer-facing summaries without changing the meaning of matrix
cells.
"""

from __future__ import annotations

from typing import Any

import numpy as np


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
        'matrix': matrix.tolist(),
    }
