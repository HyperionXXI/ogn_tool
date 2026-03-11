import math
import pandas as pd
import numpy as np


def compute_radio_horizon(station_height_m, aircraft_height_m):
    d_km = 3.57 * (math.sqrt(station_height_m) + math.sqrt(aircraft_height_m))
    return {"radio_horizon_km": float(d_km)}


def _haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    lat1r = np.deg2rad(lat1)
    lon1r = np.deg2rad(lon1)
    lat2r = np.deg2rad(lat2)
    lon2r = np.deg2rad(lon2)
    dlat = lat2r - lat1r
    dlon = lon2r - lon1r
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1r) * np.cos(lat2r) * np.sin(dlon / 2.0) ** 2
    c = 2.0 * np.arcsin(np.sqrt(a))
    return r * c


def compute_expected_vs_observed_range(df, station_height_m=10, aircraft_height_m=1200):
    if df is None or len(df) == 0:
        return {
            "radio_horizon_km": float(compute_radio_horizon(station_height_m, aircraft_height_m)["radio_horizon_km"]),
            "observed_max_km": None,
            "observed_p95_km": None,
            "coverage_efficiency": None,
        }

    horizon = compute_radio_horizon(station_height_m, aircraft_height_m)["radio_horizon_km"]

    df_local = df.copy()
    if "distance_km" not in df_local.columns:
        if all(c in df_local.columns for c in ["lat", "lon"]):
            lat0 = df_local["lat"].iloc[0]
            lon0 = df_local["lon"].iloc[0]
            df_local["distance_km"] = _haversine_km(lat0, lon0, df_local["lat"].astype(float), df_local["lon"].astype(float))
        else:
            df_local["distance_km"] = np.nan

    dist = pd.to_numeric(df_local.get("distance_km"), errors="coerce")
    dist = dist[np.isfinite(dist)]
    observed_max = float(dist.max()) if len(dist) else None
    observed_p95 = float(np.nanpercentile(dist, 95)) if len(dist) else None

    if observed_p95 is None or horizon == 0:
        efficiency = None
    else:
        efficiency = float(observed_p95 / horizon)

    return {
        "radio_horizon_km": float(horizon),
        "observed_max_km": observed_max,
        "observed_p95_km": observed_p95,
        "coverage_efficiency": efficiency,
    }
