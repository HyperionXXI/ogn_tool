from __future__ import annotations

from typing import Iterable

import numpy as np


def haversine_km_vector(
    station_lat: float,
    station_lon: float,
    lat: Iterable[float],
    lon: Iterable[float],
) -> np.ndarray:
    """Vectorized haversine distance (km) from a station to many points."""
    r = 6371.0
    lat1_r = np.radians(float(station_lat))
    lon1_r = np.radians(float(station_lon))
    lat2_r = np.radians(np.asarray(lat, dtype=float))
    lon2_r = np.radians(np.asarray(lon, dtype=float))
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1_r) * np.cos(lat2_r) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return r * c


__all__ = ["haversine_km_vector"]
