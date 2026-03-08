from __future__ import annotations

import numpy as np
import pandas as pd


def compute_azimuth_radiation(df: pd.DataFrame, station_lat: float, station_lon: float) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()
    if station_lat is None or station_lon is None:
        return pd.DataFrame()

    lat = np.radians(pd.to_numeric(df.get("lat"), errors="coerce").to_numpy())
    lon = np.radians(pd.to_numeric(df.get("lon"), errors="coerce").to_numpy())
    slat = np.radians(float(station_lat))
    slon = np.radians(float(station_lon))

    dlon = lon - slon
    x = np.sin(dlon) * np.cos(lat)
    y = np.cos(slat) * np.sin(lat) - np.sin(slat) * np.cos(lat) * np.cos(dlon)

    azimuth = (np.degrees(np.arctan2(x, y)) + 360.0) % 360.0

    df = df.copy()
    df["azimuth"] = azimuth
    df["az_bin"] = (df["azimuth"] // 10) * 10

    stats = (
        df.groupby("az_bin", as_index=False)
        .agg(
            packet_count=("distance_km", "count"),
            p95_distance_km=("distance_km", lambda x: np.percentile(x, 95)),
            mean_distance_km=("distance_km", "mean"),
        )
        .sort_values("az_bin")
    )
    return stats
