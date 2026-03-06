"""
RF feature module: Altitude vs distance.
See docs/rf_features/03_altitude_vs_distance.md
"""

from __future__ import annotations

from typing import Any, Dict

import re
import numpy as np
import pandas as pd


ALT_RE = re.compile(r"A=([0-9]+)")


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
        return {"implemented": False, "summary": {}, "data": None}

    df = df_packets.copy()
    if "raw" not in df.columns or "lat" not in df.columns or "lon" not in df.columns:
        return {"implemented": False, "summary": {}, "data": None}

    df["altitude_ft"] = df["raw"].astype(str).str.extract(ALT_RE, expand=False)
    df["altitude_ft"] = pd.to_numeric(df["altitude_ft"], errors="coerce")
    df = df.dropna(subset=["altitude_ft"])
    if df.empty:
        return {"implemented": False, "summary": {}, "data": None}

    lat = pd.to_numeric(df["lat"], errors="coerce").to_numpy()
    lon = pd.to_numeric(df["lon"], errors="coerce").to_numpy()
    alt_ft = pd.to_numeric(df["altitude_ft"], errors="coerce").to_numpy()

    dist = _haversine_km(float(station_lat), float(station_lon), lat, lon)
    alt_m = alt_ft * 0.3048
    valid = (dist > 0) & (alt_m > 0) & np.isfinite(dist) & np.isfinite(alt_m)
    if not valid.any():
        return {"implemented": False, "summary": {}, "data": None}

    dist = dist[valid]
    alt_m = alt_m[valid]

    data = pd.DataFrame({"distance_km": dist, "altitude_m": alt_m})
    packet_total = int(len(data))
    max_distance_km = float(np.max(dist)) if packet_total else None
    mean_altitude_m = float(np.mean(alt_m)) if packet_total else None
    p95_distance_km = float(np.percentile(dist, 95)) if packet_total else None

    bins = [0, 500, 1000, 2000, np.inf]
    labels = ["0-500 m", "500-1000 m", "1000-2000 m", ">2000 m"]
    data_bins = data.copy()
    data_bins["altitude_bin"] = pd.cut(data_bins["altitude_m"], bins=bins, labels=labels, right=False)
    binned = (
        data_bins.groupby("altitude_bin", observed=True, as_index=False)
        .agg(
            distance_mean_km=("distance_km", "mean"),
            distance_p95_km=("distance_km", lambda x: np.percentile(x, 95)),
            distance_max_km=("distance_km", "max"),
            sample_count=("distance_km", "size"),
        )
    )

    return {
        "implemented": True,
        "summary": {
            "packet_total": packet_total,
            "max_distance_km": max_distance_km,
            "mean_altitude_m": mean_altitude_m,
            "p95_distance_km": p95_distance_km,
        },
        "data": data.sample(n=min(len(data), 20000)),
        "binned_data": binned,
    }
