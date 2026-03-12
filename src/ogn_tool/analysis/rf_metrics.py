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


def compute_bearing(lat1: float, lon1: float, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    lat1_r = np.radians(lat1)
    lon1_r = np.radians(lon1)
    lat2_r = np.radians(lat2)
    lon2_r = np.radians(lon2)
    dlon = lon2_r - lon1_r
    y = np.sin(dlon) * np.cos(lat2_r)
    x = np.cos(lat1_r) * np.sin(lat2_r) - np.sin(lat1_r) * np.cos(lat2_r) * np.cos(dlon)
    brng = np.degrees(np.arctan2(y, x))
    return (brng + 360.0) % 360.0


def compute_distance_bearing(
    lat1: float,
    lon1: float,
    lat2: np.ndarray,
    lon2: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    dist = _haversine_km(lat1, lon1, lat2, lon2)
    bearing = compute_bearing(lat1, lon1, lat2, lon2)
    return dist, bearing


def summarize_observation_vectors(df: pd.DataFrame) -> dict:
    """Summarize RF observation vectors using distance/bearing/horizon only."""
    if df is None or len(df) == 0:
        return {
            "count": 0,
            "distance_p95_km": None,
            "distance_max_km": None,
            "bearing_coverage_bins": 0,
            "horizon_median_km": None,
            "efficiency_p95": None,
        }

    local = pd.DataFrame(df).copy()
    local["distance_km"] = pd.to_numeric(local.get("distance_km", local.get("distance")), errors="coerce")
    local["bearing_deg"] = pd.to_numeric(local.get("bearing_deg", local.get("bearing")), errors="coerce")
    local["radio_horizon_km"] = pd.to_numeric(local.get("radio_horizon_km"), errors="coerce")

    dist = local["distance_km"].dropna()
    bearing = local["bearing_deg"].dropna()
    horizon = local["radio_horizon_km"].dropna()

    if len(dist) == 0:
        return {
            "count": int(len(local)),
            "distance_p95_km": None,
            "distance_max_km": None,
            "bearing_coverage_bins": int(((bearing % 360) // 10).nunique()) if len(bearing) else 0,
            "horizon_median_km": float(horizon.median()) if len(horizon) else None,
            "efficiency_p95": None,
        }

    p95 = float(np.percentile(dist, 95))
    max_d = float(dist.max())
    horizon_med = float(horizon.median()) if len(horizon) else None
    efficiency = (p95 / horizon_med) if horizon_med and horizon_med > 0 else None

    return {
        "count": int(len(local)),
        "distance_p95_km": p95,
        "distance_max_km": max_d,
        "bearing_coverage_bins": int(((bearing % 360) // 10).nunique()) if len(bearing) else 0,
        "horizon_median_km": horizon_med,
        "efficiency_p95": float(efficiency) if efficiency is not None else None,
    }


def compute_altitude_delta(
    df: pd.DataFrame,
    altitude_col: str = "altitude_m",
    receiver_alt_col: str = "receiver_alt",
    station_alt_m: float | None = None,
) -> pd.Series:
    if df is None or df.empty or altitude_col not in df.columns:
        return pd.Series([np.nan] * (0 if df is None else len(df)), index=None if df is None else df.index)

    alt = pd.to_numeric(df.get(altitude_col), errors="coerce")
    if station_alt_m is not None:
        return alt - float(station_alt_m)
    if receiver_alt_col in df.columns:
        recv_alt = pd.to_numeric(df.get(receiver_alt_col), errors="coerce")
        return alt - recv_alt
    return pd.Series([np.nan] * len(df), index=df.index)


# Legacy compatibility helpers (kept for existing callers)
def compute_distance(df: pd.DataFrame, station_lat: float, station_lon: float) -> pd.DataFrame:
    if df is None or df.empty:
        return df
    if station_lat is None or station_lon is None:
        return df
    if "distance_km" in df.columns:
        return df
    if "lat" not in df.columns or "lon" not in df.columns:
        return df
    lat = pd.to_numeric(df.get("lat"), errors="coerce").to_numpy()
    lon = pd.to_numeric(df.get("lon"), errors="coerce").to_numpy()
    dist = _haversine_km(float(station_lat), float(station_lon), lat, lon)
    out = df.copy()
    out["distance_km"] = dist
    return out
