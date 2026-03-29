from __future__ import annotations

import pandas as pd

from ogn_tool.kernel.rf.geometry import bearing_deg_vector, haversine_km_vector


def build_rf_observations(packets_df: pd.DataFrame, receptions_df: pd.DataFrame) -> pd.DataFrame:
    """
    Join packets with rf_receptions to form RF observation rows.
    """
    if packets_df is None or receptions_df is None or packets_df.empty or receptions_df.empty:
        return pd.DataFrame()

    df = receptions_df.merge(
        packets_df,
        left_on="packet_id",
        right_on="id",
        how="left",
        suffixes=("", "_pkt"),
    )
    if "receiver" in df.columns and "igate" not in df.columns:
        df["igate"] = df["receiver"]
    return df


def compute_distance(df: pd.DataFrame, station_lat: float, station_lon: float) -> pd.Series:
    if df is None or df.empty or "lat" not in df.columns or "lon" not in df.columns:
        return pd.Series(dtype=float)
    lat = pd.to_numeric(df["lat"], errors="coerce").to_numpy()
    lon = pd.to_numeric(df["lon"], errors="coerce").to_numpy()
    distance_km = haversine_km_vector(station_lat, station_lon, lat, lon)
    return pd.Series(distance_km)


def compute_bearing(df: pd.DataFrame, station_lat: float, station_lon: float) -> pd.Series:
    if df is None or df.empty or "lat" not in df.columns or "lon" not in df.columns:
        return pd.Series(dtype=float)
    lat = pd.to_numeric(df["lat"], errors="coerce").to_numpy()
    lon = pd.to_numeric(df["lon"], errors="coerce").to_numpy()
    bearing_deg = bearing_deg_vector(station_lat, station_lon, lat, lon)
    return pd.Series(bearing_deg)
