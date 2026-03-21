from __future__ import annotations

import numpy as np
import pandas as pd


REQUIRED_CANDIDATE_COLUMNS = {"lat", "lon"}
REQUIRED_OBSERVATION_COLUMNS = {"lat", "lon", "station_id"}


def _distance_km(lat1, lon1, lat2, lon2):
    """Approximate distance in km using equirectangular approximation."""
    r_km = 6371.0

    lat1 = np.radians(lat1)
    lat2 = np.radians(lat2)
    lon1 = np.radians(lon1)
    lon2 = np.radians(lon2)

    x = (lon2 - lon1) * np.cos((lat1 + lat2) / 2)
    y = lat2 - lat1

    return r_km * np.sqrt(x * x + y * y)


def simulate_station_addition(
    candidates: pd.DataFrame,
    observations: pd.DataFrame,
    *,
    grid_resolution: float = 0.02,
    coverage_radius_km: float = 25.0,
) -> pd.DataFrame:
    """Simulate the addition of candidate stations and estimate coverage gain."""
    missing_candidates = REQUIRED_CANDIDATE_COLUMNS - set(candidates.columns)
    if missing_candidates:
        raise ValueError(f"Missing candidate columns: {missing_candidates}")

    missing_obs = REQUIRED_OBSERVATION_COLUMNS - set(observations.columns)
    if missing_obs:
        raise ValueError(f"Missing observation columns: {missing_obs}")

    obs = observations[["lat", "lon", "station_id"]].copy()
    obs["lat"] = pd.to_numeric(obs["lat"], errors="coerce")
    obs["lon"] = pd.to_numeric(obs["lon"], errors="coerce")
    obs = obs.dropna(subset=["lat", "lon", "station_id"])

    if obs.empty:
        return pd.DataFrame(
            columns=[
                "lat",
                "lon",
                "aircraft_supported",
                "coverage_gain",
                "redundancy_gain",
                "priority_score",
                "notes",
            ]
        )

    obs["lat_bin"] = (obs["lat"] / grid_resolution).round() * grid_resolution
    obs["lon_bin"] = (obs["lon"] / grid_resolution).round() * grid_resolution

    redundancy = (
        obs.groupby(["lat_bin", "lon_bin"])
        .agg(station_count=("station_id", "nunique"))
        .reset_index()
    )

    results: list[dict] = []

    for _, cand in candidates.iterrows():
        lat_c = float(cand["lat"])
        lon_c = float(cand["lon"])

        dist = _distance_km(lat_c, lon_c, obs["lat"].to_numpy(), obs["lon"].to_numpy())
        supported = obs[dist <= coverage_radius_km].copy()

        aircraft_supported = int(len(supported))

        if supported.empty:
            coverage_gain = 0
            redundancy_gain = 0
        else:
            merged = supported.merge(
                redundancy,
                on=["lat_bin", "lon_bin"],
                how="left",
            )
            coverage_gain = int((merged["station_count"] == 0).sum())
            redundancy_gain = int((merged["station_count"] == 1).sum())

        priority_score = int(coverage_gain * 2 + redundancy_gain)

        results.append(
            {
                "lat": lat_c,
                "lon": lon_c,
                "aircraft_supported": aircraft_supported,
                "coverage_gain": coverage_gain,
                "redundancy_gain": redundancy_gain,
                "priority_score": priority_score,
                "notes": "empirical station addition simulation",
            }
        )

    result_df = pd.DataFrame(results)
    if result_df.empty:
        return result_df

    result_df = result_df.sort_values(
        ["priority_score", "aircraft_supported", "lat", "lon"],
        ascending=[False, False, True, True],
    ).reset_index(drop=True)
    return result_df
