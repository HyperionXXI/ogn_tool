"""
RF feature module: RSSI vs distance.
See docs/rf_features/02_rssi_vs_distance.md
"""

from __future__ import annotations

from typing import Any, Dict

import re
import numpy as np
import pandas as pd


RSSI_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)dB")


def _haversine_km_vector(
    station_lat: float,
    station_lon: float,
    lat: np.ndarray,
    lon: np.ndarray,
) -> np.ndarray:
    r = 6371.0
    lat1_r = np.radians(float(station_lat))
    lon1_r = np.radians(float(station_lon))
    lat2_r = np.radians(np.asarray(lat, dtype=float))
    lon2_r = np.radians(np.asarray(lon, dtype=float))
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1_r) * np.cos(lat2_r) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return r * c




def haversine_km_vector(
    station_lat: float,
    station_lon: float,
    lat: np.ndarray,
    lon: np.ndarray,
) -> np.ndarray:
    """Public vectorized haversine helper used by legacy RF dataset builders."""
    return _haversine_km_vector(station_lat, station_lon, lat, lon)


def analyze(
    df_observations: pd.DataFrame,
    station_lat: float | None = None,
    station_lon: float | None = None,
    **_: Any,
) -> Dict[str, Any]:
    if df_observations is None or df_observations.empty:
        return {
            "implemented": False,
            "summary": {"input_rows": 0, "rssi_rows": 0, "distance_rows": 0},
            "data": None,
        }

    df = df_observations.copy()
    input_rows = int(len(df))

    # Vector-first path: use precomputed observation distances when available.
    if "distance_km" in df.columns:
        dist = pd.to_numeric(df["distance_km"], errors="coerce").to_numpy()
    elif "distance" in df.columns:
        dist = pd.to_numeric(df["distance"], errors="coerce").to_numpy()
    elif station_lat is not None and station_lon is not None and "lat" in df.columns and "lon" in df.columns:
        lat = pd.to_numeric(df["lat"], errors="coerce").to_numpy()
        lon = pd.to_numeric(df["lon"], errors="coerce").to_numpy()
        dist = _haversine_km_vector(float(station_lat), float(station_lon), lat, lon)
    else:
        return {
            "implemented": False,
            "summary": {"input_rows": input_rows, "rssi_rows": 0, "distance_rows": 0},
            "data": None,
        }

    if "snr" in df.columns:
        rssi = pd.to_numeric(df["snr"], errors="coerce").to_numpy()
    elif "snr_db" in df.columns:
        rssi = pd.to_numeric(df["snr_db"], errors="coerce").to_numpy()
    else:
        return {
            "implemented": False,
            "summary": {"input_rows": input_rows, "rssi_rows": 0, "distance_rows": 0},
            "data": None,
        }

    valid = (dist > 0) & np.isfinite(dist) & np.isfinite(rssi)
    distance_rows = int(np.count_nonzero(valid))
    rssi_rows = int(np.count_nonzero(np.isfinite(rssi)))
    if not valid.any():
        return {
            "implemented": False,
            "summary": {
                "input_rows": input_rows,
                "rssi_rows": rssi_rows,
                "distance_rows": distance_rows,
            },
            "data": None,
        }

    dist = dist[valid]
    rssi = rssi[valid]

    data = pd.DataFrame({"distance_km": dist, "rssi_db": rssi})
    packet_total = int(len(data))
    max_distance_km = float(np.max(dist)) if packet_total else None
    mean_rssi = float(np.mean(rssi)) if packet_total else None
    p95_distance_km = float(np.percentile(dist, 95)) if packet_total else None

    df_plot = data.sample(n=min(len(data), 20000))

    bin_size_km = 10
    data_bins = data.copy()
    data_bins["distance_bin_km"] = (data_bins["distance_km"] // bin_size_km) * bin_size_km
    binned = (
        data_bins.groupby("distance_bin_km", as_index=False)
        .agg(
            rssi_median=("rssi_db", "median"),
            rssi_p90=("rssi_db", lambda x: np.percentile(x, 90)),
            sample_count=("rssi_db", "size"),
        )
        .sort_values("distance_bin_km")
    )

    return {
        "implemented": True,
        "summary": {
            "packet_total": packet_total,
            "max_distance_km": max_distance_km,
            "mean_rssi": mean_rssi,
            "p95_distance_km": p95_distance_km,
            "input_rows": input_rows,
            "rssi_rows": rssi_rows,
            "distance_rows": distance_rows,
        },
        "data": df_plot,
        "binned_data": binned,
    }
