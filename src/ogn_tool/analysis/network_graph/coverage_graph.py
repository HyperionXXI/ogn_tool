from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def _observations_to_frame(observations) -> pd.DataFrame:
    if observations is None:
        return pd.DataFrame(columns=["station_id", "lat", "lon"])
    if isinstance(observations, dict):
        vectors = observations.get("vectors")
        if vectors is not None and len(vectors) > 0:
            observations = vectors
        else:
            observations = observations.get("distance_df")
    if isinstance(observations, pd.DataFrame):
        df = observations.copy()
    elif isinstance(observations, Iterable) and not isinstance(observations, (str, bytes, dict)):
        rows = []
        for obs in observations:
            rows.append(
                {
                    "station_id": getattr(obs, "station_id", None),
                    "lat": getattr(obs, "lat", None),
                    "lon": getattr(obs, "lon", None),
                }
            )
        df = pd.DataFrame(rows)
    else:
        df = pd.DataFrame(columns=["station_id", "lat", "lon"])

    if "station_id" not in df.columns and "igate" in df.columns:
        df["station_id"] = df["igate"]
    for col in ["station_id", "lat", "lon"]:
        if col not in df.columns:
            df[col] = pd.NA
    return df[["station_id", "lat", "lon"]].copy()


def build_coverage_graph(observations, grid_size_deg: float = 0.05) -> pd.DataFrame:
    """
    Build station-to-grid coverage links from RF observations.

    Each row represents one unique station -> grid cell relation with an
    observation count for that cell.
    """

    df = _observations_to_frame(observations)
    if df.empty:
        return pd.DataFrame(columns=["station_id", "grid_id", "grid_lat", "grid_lon", "observations"])

    df = df.dropna(subset=["station_id", "lat", "lon"])
    if df.empty:
        return pd.DataFrame(columns=["station_id", "grid_id", "grid_lat", "grid_lon", "observations"])

    work = df.copy()
    work["grid_lat"] = (pd.to_numeric(work["lat"], errors="coerce") / grid_size_deg).round() * grid_size_deg
    work["grid_lon"] = (pd.to_numeric(work["lon"], errors="coerce") / grid_size_deg).round() * grid_size_deg
    work = work.dropna(subset=["grid_lat", "grid_lon"])
    if work.empty:
        return pd.DataFrame(columns=["station_id", "grid_id", "grid_lat", "grid_lon", "observations"])

    work["grid_id"] = work["grid_lat"].map(lambda v: f"{float(v):.5f}") + ":" + work["grid_lon"].map(
        lambda v: f"{float(v):.5f}"
    )

    coverage = (
        work.groupby(["station_id", "grid_id", "grid_lat", "grid_lon"], dropna=False)
        .size()
        .reset_index(name="observations")
    )
    return coverage
