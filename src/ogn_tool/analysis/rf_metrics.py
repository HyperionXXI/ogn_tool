from __future__ import annotations

import numpy as np
import pandas as pd


def _haversine_km(lat1: float, lon1: float, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    r = 6371.0
    lat1_r = np.radians(lat1)
    lon1_r = np.radians(lon1)
    lat2_r = np.radians(lat2)
    lon2_r = np.radians(lon2)
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1_r) * np.cos(lat2_r) * np.sin(dlon / 2.0) ** 2
    return 2.0 * r * np.arcsin(np.sqrt(a))


def compute_distance(df: pd.DataFrame, station_lat: float, station_lon: float) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    if station_lat is None or station_lon is None:
        return df
    lat = pd.to_numeric(df.get("lat"), errors="coerce").to_numpy()
    lon = pd.to_numeric(df.get("lon"), errors="coerce").to_numpy()
    dist = _haversine_km(float(station_lat), float(station_lon), lat, lon)
    df = df.copy()
    df["distance_km"] = dist
    return df
