from __future__ import annotations

SPATIAL_COLUMNS = [
    "station_id",
    "lat",
    "lon",
]

VISIBILITY_COLUMNS = [
    "src",
    "igate",
]

SHADOW_COLUMNS = [
    "station_id",
    "bearing_deg",
    "lat",
    "lon",
    "station_lat",
    "station_lon",
]


__all__ = [
    "SPATIAL_COLUMNS",
    "VISIBILITY_COLUMNS",
    "SHADOW_COLUMNS",
]
