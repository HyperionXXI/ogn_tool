from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = {"lat", "lon"}


def detect_coverage_gaps(
    observations: pd.DataFrame,
    *,
    min_points: int = 3,
    grid_size: float = 0.02,
) -> list[dict[str, float | int]]:
    if not isinstance(observations, pd.DataFrame):
        raise ValueError("observations must be a pandas DataFrame")

    missing = REQUIRED_COLUMNS - set(observations.columns)
    if missing:
        raise ValueError(f"observations must contain columns: {sorted(missing)}")

    if grid_size <= 0:
        raise ValueError("grid_size must be > 0")

    df = observations[["lat", "lon"]].copy()
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df.dropna(subset=["lat", "lon"])

    if df.empty:
        return []

    df["grid_lat"] = (df["lat"] / grid_size).round() * grid_size
    df["grid_lon"] = (df["lon"] / grid_size).round() * grid_size

    counts = (
        df.groupby(["grid_lat", "grid_lon"])
        .size()
        .reset_index(name="observation_count")
    )

    gaps = counts[counts["observation_count"] <= min_points]

    return [
        {
            "lat": round(float(row.grid_lat), 6),
            "lon": round(float(row.grid_lon), 6),
            "observation_count": int(row.observation_count),
        }
        for row in gaps.itertuples()
    ]


__all__ = ["detect_coverage_gaps"]
