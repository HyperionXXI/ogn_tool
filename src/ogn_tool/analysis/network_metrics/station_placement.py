from __future__ import annotations

import pandas as pd

from ogn_tool.rf.geometry import haversine_km_vector

MAX_CANDIDATE_POINTS = 2000
SUPPORT_RADIUS_KM = 30.0


def extract_fragile_aircraft(network_metrics: dict | None) -> pd.DataFrame:
    network_metrics = network_metrics or {}
    visibility = network_metrics.get("visibility") or {}
    dependency = visibility.get("dependency") if isinstance(visibility, dict) else None
    matrix = visibility.get("matrix") if isinstance(visibility, dict) else None

    if not isinstance(dependency, pd.DataFrame) or dependency.empty:
        return pd.DataFrame(columns=["aircraft_id", "lat", "lon", "station_count", "critical_station_id"])
    if not isinstance(matrix, pd.DataFrame) or matrix.empty:
        return pd.DataFrame(columns=["aircraft_id", "lat", "lon", "station_count", "critical_station_id"])

    aircraft_positions = (
        matrix.groupby("src", dropna=False)
        .agg(lat=("lat", "mean"), lon=("lon", "mean"))
        .reset_index()
        .rename(columns={"src": "aircraft_id"})
    ) if {"src", "lat", "lon"}.issubset(matrix.columns) else pd.DataFrame(columns=["aircraft_id", "lat", "lon"])

    fragile = dependency.copy()
    fragile = fragile[fragile["station_count"] <= 2].copy() if "station_count" in fragile.columns else fragile.iloc[0:0].copy()
    if fragile.empty:
        return pd.DataFrame(columns=["aircraft_id", "lat", "lon", "station_count", "critical_station_id"])

    fragile = fragile.merge(aircraft_positions, on="aircraft_id", how="left")
    return fragile[["aircraft_id", "lat", "lon", "station_count", "critical_station_id"]].copy()


def score_candidate_location(candidate: pd.Series, fragile_aircraft: pd.DataFrame, network_metrics: dict | None) -> dict:
    network_metrics = network_metrics or {}
    station_influence = network_metrics.get("station_influence")

    lat = float(candidate["lat"])
    lon = float(candidate["lon"])

    if fragile_aircraft is None or fragile_aircraft.empty:
        return {
            "lat": lat,
            "lon": lon,
            "coverage_gain": 0.0,
            "redundancy_gain": 0.0,
            "aircraft_supported": 0,
            "critical_aircraft_supported": 0,
            "nearest_station_distance_km": 0.0,
            "placement_score": 0.0,
        }

    df = fragile_aircraft.dropna(subset=["lat", "lon"]).copy()
    if df.empty:
        return {
            "lat": lat,
            "lon": lon,
            "coverage_gain": 0.0,
            "redundancy_gain": 0.0,
            "aircraft_supported": 0,
            "critical_aircraft_supported": 0,
            "nearest_station_distance_km": 0.0,
            "placement_score": 0.0,
        }

    distances = haversine_km_vector(lat, lon, df["lat"].to_numpy(), df["lon"].to_numpy())
    supported = df[distances <= SUPPORT_RADIUS_KM].copy()

    aircraft_supported = int(len(supported))
    critical_aircraft_supported = int((supported["station_count"] <= 1).sum()) if "station_count" in supported.columns else 0
    coverage_gain = float(aircraft_supported)
    redundancy_gain = float((supported["station_count"] <= 2).sum()) if "station_count" in supported.columns else 0.0

    nearest_station_distance_km = 0.0
    if isinstance(station_influence, pd.DataFrame) and not station_influence.empty and {"lat", "lon"}.issubset(station_influence.columns):
        station_coords = station_influence.dropna(subset=["lat", "lon"])
        if not station_coords.empty:
            station_dist = haversine_km_vector(lat, lon, station_coords["lat"].to_numpy(), station_coords["lon"].to_numpy())
            nearest_station_distance_km = float(station_dist.min()) if len(station_dist) else 0.0

    placement_score = float(coverage_gain + 0.5 * redundancy_gain + 0.5 * critical_aircraft_supported)

    return {
        "lat": lat,
        "lon": lon,
        "coverage_gain": coverage_gain,
        "redundancy_gain": redundancy_gain,
        "aircraft_supported": aircraft_supported,
        "critical_aircraft_supported": critical_aircraft_supported,
        "nearest_station_distance_km": nearest_station_distance_km,
        "placement_score": placement_score,
    }


def compute_optimal_station_locations(network_metrics, candidate_grid: pd.DataFrame) -> pd.DataFrame:
    if candidate_grid is None or candidate_grid.empty or not {"lat", "lon"}.issubset(candidate_grid.columns):
        return pd.DataFrame(columns=[
            "lat",
            "lon",
            "coverage_gain",
            "redundancy_gain",
            "aircraft_supported",
            "critical_aircraft_supported",
            "nearest_station_distance_km",
            "placement_score",
        ])

    candidates = candidate_grid[["lat", "lon"]].copy()
    if len(candidates) > MAX_CANDIDATE_POINTS:
        candidates = candidates.sample(MAX_CANDIDATE_POINTS, random_state=42).reset_index(drop=True)

    fragile_aircraft = extract_fragile_aircraft(network_metrics)
    rows = [score_candidate_location(row, fragile_aircraft, network_metrics) for _, row in candidates.iterrows()]
    if not rows:
        return pd.DataFrame(columns=[
            "lat",
            "lon",
            "coverage_gain",
            "redundancy_gain",
            "aircraft_supported",
            "critical_aircraft_supported",
            "nearest_station_distance_km",
            "placement_score",
        ])

    return pd.DataFrame(rows).sort_values("placement_score", ascending=False).reset_index(drop=True)
