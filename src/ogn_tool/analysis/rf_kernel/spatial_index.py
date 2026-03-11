from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, Tuple

from .geometry import compute_distance_bearing_scalar


@dataclass
class RFSpatialIndex:
    """Grid-based cache for station-to-position distance/bearing lookups."""

    station_coords: Dict[str, Tuple[float, float, float | None]] = field(default_factory=dict)
    grid_size: float = 0.01
    _cache: Dict[tuple[str, int, int], tuple[float, float]] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        self.grid_size = max(1e-6, float(self.grid_size))

    def _cell_for(self, lat: float, lon: float) -> tuple[int, int]:
        # Required indexing rule: floor(lat/grid_size), floor(lon/grid_size)
        cell_lat = int(math.floor(float(lat) / self.grid_size))
        cell_lon = int(math.floor(float(lon) / self.grid_size))
        return cell_lat, cell_lon

    def _cell_center(self, cell_lat: int, cell_lon: int) -> tuple[float, float]:
        return (
            (float(cell_lat) + 0.5) * self.grid_size,
            (float(cell_lon) + 0.5) * self.grid_size,
        )

    def register_station(self, station_id: str, lat: float, lon: float, alt: float | None = None) -> None:
        self.station_coords[str(station_id)] = (float(lat), float(lon), alt)

    def precompute_cells(self, station_id: str, cells: Iterable[tuple[int, int]]) -> None:
        if station_id not in self.station_coords:
            return
        st_lat, st_lon, _ = self.station_coords[station_id]
        for cell_lat, cell_lon in cells:
            key = (station_id, int(cell_lat), int(cell_lon))
            if key in self._cache:
                continue
            c_lat, c_lon = self._cell_center(int(cell_lat), int(cell_lon))
            self._cache[key] = compute_distance_bearing_scalar(
                station_lat=st_lat,
                station_lon=st_lon,
                aircraft_lat=c_lat,
                aircraft_lon=c_lon,
            )

    def get_distance_bearing(self, station_id: str, lat: float, lon: float) -> tuple[float | None, float | None]:
        station_id = str(station_id)
        if station_id not in self.station_coords:
            return None, None

        cell_lat, cell_lon = self._cell_for(float(lat), float(lon))
        key = (station_id, cell_lat, cell_lon)

        value = self._cache.get(key)
        if value is None:
            self.precompute_cells(station_id, [(cell_lat, cell_lon)])
            value = self._cache.get(key)

        if value is None:
            return None, None

        return float(value[0]), float(value[1])


__all__ = ["RFSpatialIndex"]
