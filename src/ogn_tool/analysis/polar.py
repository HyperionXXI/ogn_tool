"""
RF feature module: polar coverage.
See docs/rf_features/01_polar_coverage.md
"""

from __future__ import annotations

from typing import Any, Dict

import math
import os
import numpy as np
import pandas as pd


def _bearing_deg(lat1: float, lon1: float, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    lat1_r = np.radians(lat1)
    lon1_r = np.radians(lon1)
    lat2_r = np.radians(lat2)
    lon2_r = np.radians(lon2)
    dlon = lon2_r - lon1_r
    y = np.sin(dlon) * np.cos(lat2_r)
    x = np.cos(lat1_r) * np.sin(lat2_r) - np.sin(lat1_r) * np.cos(lat2_r) * np.cos(dlon)
    brng = np.degrees(np.arctan2(y, x))
    return (brng + 360.0) % 360.0


def analyze(
    df_grid: pd.DataFrame,
    station_lat: float | None = None,
    station_lon: float | None = None,
    **_: Any,
) -> Dict[str, Any]:
    if df_grid is None or df_grid.empty:
        return {
            "implemented": True,
            "summary": {"bins": 0, "packet_total": 0},
            "data": None,
        }

    if station_lat is None or station_lon is None:
        env_lat = os.getenv("OGN_STATION_LAT")
        env_lon = os.getenv("OGN_STATION_LON")
        if env_lat is not None and env_lon is not None:
            station_lat = float(env_lat)
            station_lon = float(env_lon)
    if station_lat is None or station_lon is None:
        return {
            "implemented": True,
            "summary": {"bins": 0, "packet_total": 0},
            "data": None,
        }

    lat = pd.to_numeric(df_grid.get("lat"), errors="coerce").to_numpy()
    lon = pd.to_numeric(df_grid.get("lon"), errors="coerce").to_numpy()
    pkt = pd.to_numeric(df_grid.get("packet_count"), errors="coerce").to_numpy()
    dist = pd.to_numeric(df_grid.get("max_distance_km"), errors="coerce").to_numpy()
    rssi = pd.to_numeric(df_grid.get("best_rssi_db"), errors="coerce").to_numpy()

    mask = np.isfinite(lat) & np.isfinite(lon) & np.isfinite(pkt)
    if not mask.any():
        return {
            "implemented": True,
            "summary": {"bins": 0, "packet_total": 0},
            "data": None,
        }

    lat = lat[mask]
    lon = lon[mask]
    pkt = pkt[mask]
    dist = dist[mask]
    rssi = rssi[mask]

    az = _bearing_deg(station_lat, station_lon, lat, lon)
    bin_size = 10.0
    bins = (az // bin_size).astype(int)

    df = pd.DataFrame(
        {
            "azimuth_bin": bins,
            "packet_count": pkt,
            "max_distance_km": dist,
            "best_rssi_db": rssi,
        }
    )

    agg = (
        df.groupby("azimuth_bin", as_index=False)
        .agg(
            packet_count=("packet_count", "sum"),
            max_distance_km=("max_distance_km", "max"),
            best_rssi_db=("best_rssi_db", "max"),
        )
        .sort_values("azimuth_bin")
    )

    return {
        "implemented": True,
        "summary": {
            "bins": int(agg["azimuth_bin"].nunique()),
            "packet_total": int(np.nansum(agg["packet_count"])) if not agg.empty else 0,
            "bin_size_deg": bin_size,
        },
        "data": agg,
    }
