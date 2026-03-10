from __future__ import annotations

import numpy as np
import pandas as pd


def compute_azimuth_footprint(
    df_observations: pd.DataFrame,
    station_lat: float,
    station_lon: float,
    bin_deg: int = 10,
    min_samples: int = 50,
) -> dict:
    if df_observations is None or df_observations.empty:
        return {"implemented": False, "summary": {"reason": "no_packets"}, "data": None}
    if station_lat is None or station_lon is None:
        return {"implemented": False, "summary": {"reason": "no_station_coords"}, "data": None}
    if "lat" not in df_observations.columns or "lon" not in df_observations.columns or "distance_km" not in df_observations.columns:
        return {"implemented": False, "summary": {"reason": "missing_columns"}, "data": None}

    lat = np.radians(pd.to_numeric(df_observations["lat"], errors="coerce").to_numpy())
    lon = np.radians(pd.to_numeric(df_observations["lon"], errors="coerce").to_numpy())
    slat = np.radians(float(station_lat))
    slon = np.radians(float(station_lon))
    dlon = lon - slon
    x = np.sin(dlon) * np.cos(lat)
    y = np.cos(slat) * np.sin(lat) - np.sin(slat) * np.cos(lat) * np.cos(dlon)
    azimuth = (np.degrees(np.arctan2(x, y)) + 360.0) % 360.0

    df = df_observations.copy()
    df["azimuth"] = azimuth
    df["az_bin"] = (df["azimuth"] // bin_deg) * bin_deg

    agg = (
        df.groupby("az_bin", as_index=False)
        .agg(
            packet_count=("distance_km", "count"),
            max_distance_km=("distance_km", "max"),
            p95_distance_km=("distance_km", lambda x: np.percentile(x, 95)),
        )
        .sort_values("az_bin")
    )
    valid = agg[agg["packet_count"] >= min_samples]
    if valid.empty:
        return {"implemented": False, "summary": {"reason": "insufficient_samples"}, "data": agg}

    summary = {
        "bin_deg": bin_deg,
        "sector_count": int(len(valid)),
        "max_distance_km": float(valid["max_distance_km"].max()),
        "p95_distance_km": float(valid["p95_distance_km"].max()),
        "min_samples": int(min_samples),
    }
    return {"implemented": True, "summary": summary, "data": agg}
