from __future__ import annotations

import pandas as pd


def detect_rf_blind_zones(df: pd.DataFrame, distance_bin_km: float = 5.0, azimuth_bin_deg: float = 10.0):
    """Detect blind zones from observation vectors.

    Uses only vector metrics:
    - distance_km
    - bearing_deg
    - radio_horizon_km
    """
    if df is None or len(df) == 0:
        return pd.DataFrame(
            columns=[
                "distance_bin",
                "azimuth_bin",
                "observations",
                "horizon_mean_km",
                "distance_mean_km",
                "blind_score",
                "blind_zone",
            ]
        )

    local = pd.DataFrame(df).copy()
    mode = (
        "vector"
        if {"distance_km", "bearing_deg", "radio_horizon_km"} <= set(local.columns)
        else "packet"
    )

    if mode == "packet":
        src_col = "src" if "src" in local.columns else ("aircraft_id" if "aircraft_id" in local.columns else None)
        station_col = "igate" if "igate" in local.columns else ("station_id" if "station_id" in local.columns else None)
        if src_col is None or station_col is None or "lat" not in local.columns or "lon" not in local.columns:
            return pd.DataFrame(columns=["blind_score", "blind_zone", "mode"])

        local["lat"] = pd.to_numeric(local["lat"], errors="coerce")
        local["lon"] = pd.to_numeric(local["lon"], errors="coerce")
        local = local.dropna(subset=["lat", "lon"])
        if local.empty:
            return pd.DataFrame(columns=["blind_score", "blind_zone", "mode"])

        # Approximate km->degree conversion at mid-latitudes.
        grid_size_deg = float(distance_bin_km) / 111.0
        local["grid_lat"] = (local["lat"] / grid_size_deg).round() * grid_size_deg
        local["grid_lon"] = (local["lon"] / grid_size_deg).round() * grid_size_deg

        grid = (
            local.groupby(["grid_lat", "grid_lon"], dropna=False)
            .agg(
                aircraft=(src_col, "nunique"),
                stations=(station_col, "nunique"),
                packets=(src_col, "size"),
            )
            .reset_index()
        )
        grid["blind_score"] = grid["aircraft"] / (grid["stations"] + 1)
        grid["blind_zone"] = grid["blind_score"] > 3
        grid["mode"] = mode
        return grid

    local["distance_km"] = pd.to_numeric(local.get("distance_km", local.get("distance")), errors="coerce")
    local["bearing_deg"] = pd.to_numeric(local.get("bearing_deg", local.get("bearing")), errors="coerce")
    local["radio_horizon_km"] = pd.to_numeric(local.get("radio_horizon_km"), errors="coerce")

    local = local.dropna(subset=["distance_km", "bearing_deg"])
    if local.empty:
        return pd.DataFrame(
            columns=[
                "distance_bin",
                "azimuth_bin",
                "observations",
                "horizon_mean_km",
                "distance_mean_km",
                "blind_score",
                "blind_zone",
                "mode",
            ]
        )

    local["distance_bin"] = (local["distance_km"] // float(distance_bin_km)) * float(distance_bin_km)
    local["azimuth_bin"] = (local["bearing_deg"] // float(azimuth_bin_deg)) * float(azimuth_bin_deg)

    grouped = (
        local.groupby(["distance_bin", "azimuth_bin"], dropna=False)
        .agg(
            observations=("distance_km", "size"),
            horizon_mean_km=("radio_horizon_km", "mean"),
            distance_mean_km=("distance_km", "mean"),
        )
        .reset_index()
    )

    grouped["horizon_mean_km"] = pd.to_numeric(grouped["horizon_mean_km"], errors="coerce")
    grouped["distance_mean_km"] = pd.to_numeric(grouped["distance_mean_km"], errors="coerce")

    grouped["blind_score"] = grouped["distance_mean_km"] / grouped["horizon_mean_km"].replace(0, pd.NA)
    grouped["blind_score"] = grouped["blind_score"].fillna(0.0)
    grouped["blind_zone"] = grouped["blind_score"] > 1.0
    grouped["mode"] = mode

    return grouped
