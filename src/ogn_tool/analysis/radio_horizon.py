"""
RF feature module: Radio horizon.
See docs/rf_features/07_radio_horizon.md
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
    station_alt_m: float | None = None,
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

    alt_m = alt_ft * 0.3048
    dist = _haversine_km(float(station_lat), float(station_lon), lat, lon)

    valid = (dist > 0) & (alt_m > 0) & (alt_m <= 15000) & np.isfinite(dist) & np.isfinite(alt_m)
    if not valid.any():
        return {"implemented": False, "summary": {}, "data": None}

    dist = dist[valid]
    alt_m = alt_m[valid]

    st_alt = float(400.0 if station_alt_m is None else station_alt_m)
    horizon_km = 3.57 * (np.sqrt(np.maximum(st_alt, 0.0)) + np.sqrt(alt_m))
    horizon_theoretical_km = horizon_km.copy()
    valid_h = (horizon_km > 0) & np.isfinite(horizon_km)
    if not valid_h.any():
        return {"implemented": False, "summary": {}, "data": None}

    dist = dist[valid_h]
    alt_m = alt_m[valid_h]
    horizon_km = horizon_km[valid_h]
    ratio = dist / horizon_km

    data = pd.DataFrame(
        {
            "distance_km": dist,
            "horizon_km": horizon_km,
            "horizon_theoretical_km": horizon_theoretical_km,
            "reception_ratio": ratio,
            "altitude_m": alt_m,
        }
    )

    bins = (data["horizon_km"] // 20) * 20
    binned = (
        data.assign(horizon_bin_km=bins)
        .groupby("horizon_bin_km", as_index=False)
        .agg(
            distance_median=("distance_km", "median"),
            sample_count=("distance_km", "size"),
        )
        .sort_values("horizon_bin_km")
    )

    packet_total = int(len(data))
    summary = {
        "packet_total": packet_total,
        "station_alt_m": st_alt,
        "horizon_mean_km": float(np.mean(horizon_km)) if packet_total else None,
        "horizon_p95_km": float(np.percentile(horizon_km, 95)) if packet_total else None,
        "observed_p95_distance_km": float(np.percentile(dist, 95)) if packet_total else None,
        "efficiency_ratio": float(np.mean(ratio)) if packet_total else None,
    }

    return {
        "implemented": True,
        "summary": summary,
        "data": data.sample(n=min(len(data), 20000)),
        "binned_data": binned,
    }
