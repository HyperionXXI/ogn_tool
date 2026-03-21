from __future__ import annotations

from typing import Any, Iterable

import pandas as pd


def build_observations(
    distance_df: pd.DataFrame,
    station_lat: float,
    station_lon: float,
    vectors: Iterable[Any] | None = None,
    grid_for_analysis: pd.DataFrame | None = None,
    timestamp: Any | None = None,
    timestamp_ns: Any | None = None,
) -> dict[str, Any]:
    """Build canonical observation payload shared by RF stages."""

    return {
        "distance_df": distance_df if distance_df is not None else pd.DataFrame(),
        "grid_for_analysis": grid_for_analysis if grid_for_analysis is not None else pd.DataFrame(),
        "station_lat": station_lat,
        "station_lon": station_lon,
        "vectors": list(vectors or []),
        "timestamp": timestamp,
        "timestamp_ns": timestamp_ns,
    }
