from __future__ import annotations

from math import floor

import pandas as pd


REQUIRED_COLUMNS = {"lat", "lon"}
AIRCRAFT_ID_COLUMNS = ("aircraft_id", "src", "aircraft")


def compute_traffic_density(
    observations: pd.DataFrame,
    *,
    grid_size: float = 0.02,
) -> dict[tuple[float, float], float]:
    if not isinstance(observations, pd.DataFrame):
        raise ValueError("observations must be a pandas DataFrame")
    if grid_size <= 0:
        raise ValueError("grid_size must be > 0")

    missing = REQUIRED_COLUMNS - set(observations.columns)
    if missing:
        raise ValueError(f"observations must contain columns: {sorted(missing)}")

    work = observations[["lat", "lon"]].copy()
    work["lat"] = pd.to_numeric(work["lat"], errors="coerce")
    work["lon"] = pd.to_numeric(work["lon"], errors="coerce")
    work = work.dropna(subset=["lat", "lon"])

    density: dict[tuple[float, float], float] = {}
    for row in work.itertuples(index=False):
        cell = _cell_key(float(row.lat), float(row.lon), grid_size)
        density[cell] = density.get(cell, 0.0) + 1.0

    return density



def build_aircraft_weights(
    observations: pd.DataFrame,
    *,
    grid_size: float = 0.02,
) -> dict[str, float]:
    if not isinstance(observations, pd.DataFrame):
        raise ValueError("observations must be a pandas DataFrame")
    if grid_size <= 0:
        raise ValueError("grid_size must be > 0")

    aircraft_column = _resolve_aircraft_column(observations)
    work = observations[["lat", "lon", aircraft_column]].copy()
    work["lat"] = pd.to_numeric(work["lat"], errors="coerce")
    work["lon"] = pd.to_numeric(work["lon"], errors="coerce")
    work[aircraft_column] = work[aircraft_column].astype("string")
    work = work.dropna(subset=["lat", "lon", aircraft_column])

    density = compute_traffic_density(work[["lat", "lon"]], grid_size=grid_size)
    weights: dict[str, float] = {}

    for row in work.itertuples(index=False):
        aircraft_id = str(getattr(row, aircraft_column))
        cell = _cell_key(float(row.lat), float(row.lon), grid_size)
        cell_density = density.get(cell, 0.0)
        if cell_density <= 0:
            continue
        weight = 1.0 / cell_density
        current = weights.get(aircraft_id)
        if current is None or weight > current:
            weights[aircraft_id] = weight

    return weights



def _cell_key(lat: float, lon: float, grid_size: float) -> tuple[float, float]:
    return (
        round(floor(lat / grid_size) * grid_size, 6),
        round(floor(lon / grid_size) * grid_size, 6),
    )



def _resolve_aircraft_column(observations: pd.DataFrame) -> str:
    for name in AIRCRAFT_ID_COLUMNS:
        if name in observations.columns:
            return name
    raise ValueError("observations must contain an aircraft identifier column")


__all__ = ["compute_traffic_density", "build_aircraft_weights"]
