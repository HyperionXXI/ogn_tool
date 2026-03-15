"""Azimuth-distance RF aggregation primitives.

This module computes a deterministic azimuth-distance matrix from usable
RF observations. The output is an analytical primitive and must remain
independent from any UI or visualization concern.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


REQUIRED_BIN_EDGES = 2


def _resolve_numeric_series(observations: pd.DataFrame, primary: str, fallback: str | None = None) -> pd.Series:
    """Return a numeric series from the preferred observation column.

    Parameters
    ----------
    observations:
        Observation table containing analytical RF fields.
    primary:
        Preferred column name.
    fallback:
        Optional fallback column when the preferred column is absent.

    Returns
    -------
    pandas.Series
        Numeric values coerced with invalid entries mapped to NaN.
    """
    if primary in observations.columns:
        return pd.to_numeric(observations[primary], errors='coerce')
    if fallback and fallback in observations.columns:
        return pd.to_numeric(observations[fallback], errors='coerce')
    return pd.Series(np.nan, index=observations.index, dtype=float)


def _validate_edges(name: str, edges: np.ndarray) -> None:
    """Validate that bin edges are explicit, finite, and strictly increasing."""
    if edges.ndim != 1:
        raise ValueError(f'{name} must be one-dimensional.')
    if len(edges) < REQUIRED_BIN_EDGES:
        raise ValueError(f'{name} must contain at least two bin edges.')
    if not np.all(np.isfinite(edges)):
        raise ValueError(f'{name} must contain finite values only.')
    if not np.all(np.diff(edges) > 0):
        raise ValueError(f'{name} must be strictly increasing.')


def compute_azimuth_distance_matrix(
    observations: pd.DataFrame,
    azimuth_bins: list[float] | np.ndarray,
    distance_bins_km: list[float] | np.ndarray,
) -> dict[str, Any]:
    """Aggregate usable RF observations into an azimuth-distance matrix.

    Parameters
    ----------
    observations:
        Observation table. The function consumes `bearing_deg` or `bearing`
        and `distance_km` or `distance` when available.
    azimuth_bins:
        Explicit azimuth bin edges in degrees. Edges must be strictly
        increasing and represent bin edges, not centers.
    distance_bins_km:
        Explicit radial distance bin edges in kilometers. Edges must be
        strictly increasing and represent bin edges, not centers.

    Returns
    -------
    dict[str, Any]
        Analytical primitive with explicit bins, dense count matrix, and the
        number of represented usable observations.

    Notes
    -----
    Bin assignment follows the contract reference method:

        np.searchsorted(edges, value, side="right") - 1

    Observations outside the provided bin edges are excluded from the matrix
    and from `packet_count`. This keeps the conservation invariant true for
    represented observations:

        sum(matrix) == packet_count
    """
    azimuth_edges = np.asarray(azimuth_bins, dtype=float)
    distance_edges = np.asarray(distance_bins_km, dtype=float)
    _validate_edges('azimuth_bins', azimuth_edges)
    _validate_edges('distance_bins_km', distance_edges)

    azimuth = _resolve_numeric_series(observations, 'bearing_deg', 'bearing').to_numpy(dtype=float)
    distance = _resolve_numeric_series(observations, 'distance_km', 'distance').to_numpy(dtype=float)

    usable_mask = np.isfinite(azimuth) & np.isfinite(distance)
    if not np.any(usable_mask):
        matrix = np.zeros((len(azimuth_edges) - 1, len(distance_edges) - 1), dtype=int)
        return {
            'azimuth_bins': azimuth_edges.tolist(),
            'distance_bins_km': distance_edges.tolist(),
            'matrix': matrix.tolist(),
            'packet_count': 0,
        }

    azimuth = np.mod(azimuth[usable_mask], 360.0)
    distance = distance[usable_mask]

    azimuth_idx = np.searchsorted(azimuth_edges, azimuth, side='right') - 1
    distance_idx = np.searchsorted(distance_edges, distance, side='right') - 1

    in_range_mask = (
        (azimuth_idx >= 0)
        & (azimuth_idx < len(azimuth_edges) - 1)
        & (distance_idx >= 0)
        & (distance_idx < len(distance_edges) - 1)
    )

    azimuth_idx = azimuth_idx[in_range_mask]
    distance_idx = distance_idx[in_range_mask]

    matrix = np.zeros((len(azimuth_edges) - 1, len(distance_edges) - 1), dtype=int)
    if len(azimuth_idx):
        np.add.at(matrix, (azimuth_idx, distance_idx), 1)

    packet_count = int(matrix.sum())
    return {
        'azimuth_bins': azimuth_edges.tolist(),
        'distance_bins_km': distance_edges.tolist(),
        'matrix': matrix.tolist(),
        'packet_count': packet_count,
    }
