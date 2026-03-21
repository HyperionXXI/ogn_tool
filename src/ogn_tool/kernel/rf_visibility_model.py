from __future__ import annotations

import math


def compute_radio_horizon(station_height_m, aircraft_height_m):
    """Compute radio horizon in km from station/aircraft heights in meters."""
    try:
        station = float(station_height_m)
        aircraft = float(aircraft_height_m)
    except (TypeError, ValueError):
        return {"radio_horizon_km": 0.0}

    station = max(0.0, station)
    aircraft = max(0.0, aircraft)
    horizon = 3.57 * (math.sqrt(station) + math.sqrt(aircraft))
    return {"radio_horizon_km": float(horizon)}
