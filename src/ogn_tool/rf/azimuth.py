"""Legacy entry point for azimuth diagnostics.

This module provides a stable import surface for RF analysis code.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


__all__ = [
    "compute_azimuth_radiation",
    "compute_azimuth_histogram",
    "analyze_directional_balance",
]


def compute_azimuth_radiation(df, station_lat: float, station_lon: float):
    """Compute azimuth diagnostics without importing analysis.experimental."""
    if df is None or getattr(df, "empty", True):
        return pd.DataFrame()
    if station_lat is None or station_lon is None:
        return pd.DataFrame()

    work = df.copy()
    lat_col = pd.to_numeric(work.get("lat"), errors="coerce")
    lon_col = pd.to_numeric(work.get("lon"), errors="coerce")
    if lat_col is None or lon_col is None:
        return pd.DataFrame()

    lat = np.radians(lat_col.to_numpy())
    lon = np.radians(lon_col.to_numpy())
    slat = np.radians(float(station_lat))
    slon = np.radians(float(station_lon))

    dlon = lon - slon
    x = np.sin(dlon) * np.cos(lat)
    y = np.cos(slat) * np.sin(lat) - np.sin(slat) * np.cos(lat) * np.cos(dlon)

    azimuth = (np.degrees(np.arctan2(x, y)) + 360.0) % 360.0

    work["azimuth"] = azimuth
    work["az_bin"] = (work["azimuth"] // 10) * 10

    if "distance_km" not in work.columns:
        return (
            work.groupby("az_bin", as_index=False)
            .agg(packet_count=("azimuth", "count"))
            .sort_values("az_bin")
        )

    stats = (
        work.groupby("az_bin", as_index=False)
        .agg(
            packet_count=("distance_km", "count"),
            p95_distance_km=("distance_km", lambda x: np.percentile(x, 95)),
            mean_distance_km=("distance_km", "mean"),
        )
        .sort_values("az_bin")
    )
    return stats


def compute_azimuth_histogram(series, bins: int = 36):
    """Compute azimuth histogram for RF coverage analysis."""
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
    """Compute directional balance metric."""
    if not histogram:
        return None

    hist = np.asarray(histogram.get("hist") or [], dtype=float)
    if hist.size == 0:
        return None

    mean = hist.mean()
    if mean == 0:
        return 0.0
    return float(hist.std() / (mean + 1e-6))
