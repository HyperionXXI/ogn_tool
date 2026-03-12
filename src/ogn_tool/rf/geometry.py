from __future__ import annotations

import math
from typing import Iterable

import numpy as np


def compute_distance_bearing_scalar(
    station_lat: float,
    station_lon: float,
    aircraft_lat: float,
    aircraft_lon: float,
) -> tuple[float, float]:
    """Compute great-circle distance (km) and initial bearing (deg)."""
    r_km = 6371.0

    lat1 = math.radians(float(station_lat))
    lon1 = math.radians(float(station_lon))
    lat2 = math.radians(float(aircraft_lat))
    lon2 = math.radians(float(aircraft_lon))

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat / 2.0) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance_km = r_km * c

    x = math.sin(dlon) * math.cos(lat2)
    y = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    bearing = (math.degrees(math.atan2(x, y)) + 360.0) % 360.0

    return distance_km, bearing


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


def bearing_deg_vector(
    station_lat: float,
    station_lon: float,
    lat: Iterable[float],
    lon: Iterable[float],
) -> np.ndarray:
    """Vectorized initial bearing (deg) from station to many points."""
    lat1_r = np.radians(float(station_lat))
    lon1_r = np.radians(float(station_lon))
    lat2_r = np.radians(np.asarray(lat, dtype=float))
    lon2_r = np.radians(np.asarray(lon, dtype=float))

    dlon = lon2_r - lon1_r
    y = np.sin(dlon) * np.cos(lat2_r)
    x = np.cos(lat1_r) * np.sin(lat2_r) - np.sin(lat1_r) * np.cos(lat2_r) * np.cos(dlon)
    brng = np.degrees(np.arctan2(y, x))
    return (brng + 360.0) % 360.0


def altitude_difference(aircraft_alt_m: float | None, station_alt_m: float | None) -> float | None:
    """Compute aircraft minus station altitude difference in meters."""
    if aircraft_alt_m is None or station_alt_m is None:
        return None
    try:
        return float(aircraft_alt_m) - float(station_alt_m)
    except (TypeError, ValueError):
        return None


def radio_horizon_km(station_height_m: float, aircraft_height_m: float) -> float:
    """Classical radio horizon approximation in kilometers.

    d_km = 3.57 * (sqrt(h_station) + sqrt(h_aircraft))
    """
    h1 = max(0.0, float(station_height_m))
    h2 = max(0.0, float(aircraft_height_m))
    return float(3.57 * (math.sqrt(h1) + math.sqrt(h2)))


__all__ = [
    "compute_distance_bearing_scalar",
    "haversine_km_vector",
    "bearing_deg_vector",
    "altitude_difference",
    "radio_horizon_km",
]