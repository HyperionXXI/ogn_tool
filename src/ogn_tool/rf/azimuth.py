"""Legacy entry point for azimuth diagnostics.

This module provides a stable import surface for RF analysis code.
"""

from __future__ import annotations

import numpy as np


def compute_azimuth_radiation(df, station_lat: float, station_lon: float):
    """Lazy wrapper around the experimental azimuth implementation."""
    from ogn_tool.analysis.experimental.azimuth import compute_azimuth_radiation as _impl

    return _impl(df, station_lat, station_lon)


__all__ = [
    "compute_azimuth_radiation",
    "compute_azimuth_histogram",
    "analyze_directional_balance",
]


def compute_azimuth_histogram(series, bins: int = 36):
    """
    Compute azimuth histogram for RF coverage analysis.
    """
    if series is None:
        return None

    try:
        values = np.asarray(series, dtype=float)
    except Exception:
        return None

    values = values[~np.isnan(values)]
    if values.size == 0:
        return None

    hist, edges = np.histogram(values, bins=bins, range=(0, 360))
    return {"hist": hist.tolist(), "edges": edges.tolist()}


def analyze_directional_balance(histogram):
    """
    Compute directional balance metric.
    """
    if not histogram:
        return None

    hist = np.asarray(histogram.get("hist") or [], dtype=float)
    if hist.size == 0:
        return None

    mean = hist.mean()
    if mean == 0:
        return 0.0
    return float(hist.std() / (mean + 1e-6))
