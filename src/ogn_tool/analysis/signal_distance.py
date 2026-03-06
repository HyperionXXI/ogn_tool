"""
RF feature module: RSSI vs distance.
See docs/rf_features/02_rssi_vs_distance.md
"""

from __future__ import annotations

from typing import Any, Dict

import math
import re
import numpy as np
import pandas as pd


RSSI_RE = re.compile(r"([0-9]+(?:\.[0-9]+)?)dB")


def _haversine_km(lat1: float, lon1: float, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    r = 6371.0
    lat1_r = np.radians(lat1)
    lon1_r = np.radians(lon1)
    lat2_r = np.radians(lat2)
    lon2_r = np.radians(lon2)
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1_r) * np.cos(lat2_r) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return r * c


def analyze(
    df_packets: pd.DataFrame,
    station_lat: float | None = None,
    station_lon: float | None = None,
    **_: Any,
) -> Dict[str, Any]:
    if df_packets is None or df_packets.empty or station_lat is None or station_lon is None:
        return {
            "implemented": False,
            "summary": {"input_rows": 0, "rssi_rows": 0, "distance_rows": 0},
            "data": None,
        }

    df = df_packets.copy()
    input_rows = int(len(df))
    if "raw" not in df.columns or "lat" not in df.columns or "lon" not in df.columns:
        return {
            "implemented": False,
            "summary": {"input_rows": input_rows, "rssi_rows": 0, "distance_rows": 0},
            "data": None,
        }

    df["rssi_db"] = df["raw"].astype(str).str.extract(RSSI_RE, expand=False).astype(float)
    df = df.dropna(subset=["rssi_db"])
    rssi_rows = int(len(df))
    if df.empty:
        return {
            "implemented": False,
            "summary": {"input_rows": input_rows, "rssi_rows": rssi_rows, "distance_rows": 0},
            "data": None,
        }

    lat = pd.to_numeric(df["lat"], errors="coerce").to_numpy()
    lon = pd.to_numeric(df["lon"], errors="coerce").to_numpy()
    rssi = pd.to_numeric(df["rssi_db"], errors="coerce").to_numpy()

    dist = _haversine_km(float(station_lat), float(station_lon), lat, lon)
    valid = (dist > 0) & (rssi > 0) & np.isfinite(dist) & np.isfinite(rssi)
    distance_rows = int(np.count_nonzero(valid))
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

    # Feature 02 keeps finer 10 km bins for RF readability
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
