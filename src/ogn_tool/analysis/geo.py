from __future__ import annotations

import numpy as np
import pandas as pd

from ogn_tool.analysis.rf_metrics import compute_distance_bearing as _compute_distance_bearing


def compute_distance_bearing(
    lat_series: pd.Series | np.ndarray,
    lon_series: pd.Series | np.ndarray,
    station_lat: float,
    station_lon: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute distance (km) and bearing (degrees) from station to points.

    Args:
        lat_series: Series/array of target latitudes.
        lon_series: Series/array of target longitudes.
        station_lat: Station latitude.
        station_lon: Station longitude.

    Returns:
        Tuple of (distance_km, bearing_deg) arrays.
    """

    import numpy as _np

    if isinstance(lat_series, _np.ndarray):
        lat = lat_series.astype(float)
    else:
        lat = pd.to_numeric(lat_series, errors="coerce").to_numpy(dtype=float)

    if isinstance(lon_series, _np.ndarray):
        lon = lon_series.astype(float)
    else:
        lon = pd.to_numeric(lon_series, errors="coerce").to_numpy(dtype=float)

    distance_km, bearing_deg = _compute_distance_bearing(
        float(station_lat),
        float(station_lon),
        lat,
        lon,
    )

    return distance_km, bearing_deg
