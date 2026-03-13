from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = {"lat", "lon", "station_id"}


def detect_coverage_gaps(
    observations: pd.DataFrame,
    *,
    min_station_count: int = 2,
    grid_resolution: float = 0.02,
) -> pd.DataFrame:
    """Detect spatial coverage gaps based on station observations.

    Parameters
    ----------
    observations : pd.DataFrame
        Normalized observations containing at least:
            lat : float
            lon : float
            station_id : str

    min_station_count : int
        Minimum number of stations required for acceptable coverage.

    grid_resolution : float
        Spatial grid resolution in degrees.

    Returns
    -------
    pd.DataFrame
        Columns:
            lat
            lon
            station_count
            gap_level
            notes
    """
    missing = REQUIRED_COLUMNS - set(observations.columns)
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df = observations[["lat", "lon", "station_id"]].copy()
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df.dropna(subset=["lat", "lon", "station_id"])

    if df.empty:
        return pd.DataFrame(columns=["lat", "lon", "station_count", "gap_level", "notes"])

    df["lat_bin"] = (df["lat"] / grid_resolution).round() * grid_resolution
    df["lon_bin"] = (df["lon"] / grid_resolution).round() * grid_resolution

    grouped = (
        df.groupby(["lat_bin", "lon_bin"])
        .agg(station_count=("station_id", "nunique"))
        .reset_index()
    )

    def classify_gap(count: int) -> tuple[str, str]:
        if count == 0:
            return "CRITICAL", "no station coverage"
        if count == 1:
            return "HIGH", "single station coverage"
        if count <= min_station_count:
            return "MEDIUM", "limited redundancy"
        return "OK", "sufficient coverage"

    levels = grouped["station_count"].apply(classify_gap)
    grouped["gap_level"] = levels.apply(lambda x: x[0])
    grouped["notes"] = levels.apply(lambda x: x[1])

    result = grouped.rename(columns={"lat_bin": "lat", "lon_bin": "lon"})
    return result[["lat", "lon", "station_count", "gap_level", "notes"]]
