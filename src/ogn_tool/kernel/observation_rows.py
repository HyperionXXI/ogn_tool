from __future__ import annotations

from typing import Iterable, List

from ogn_tool.models.rf_observation_vector import RFObservationVector
from ogn_tool.models.rf_types import RFObservationEvent, rf_event_to_dataset_row


def observations_to_rows(observations: Iterable[object]) -> List[dict]:
    """Convert RF observation objects (vector/event) into analysis row dictionaries."""
    rows: List[dict] = []
    for obs in observations:
        if isinstance(obs, RFObservationVector):
            rows.append(
                {
                    "station_id": obs.station_id,
                    "aircraft": obs.aircraft_id,
                    "src": obs.aircraft_id,
                    "igate": obs.station_id,
                    "lat": obs.lat,
                    "lon": obs.lon,
                    "altitude_m": obs.altitude_m,
                    "distance_km": obs.distance_km,
                    "bearing_deg": obs.bearing_deg,
                    "radio_horizon_km": obs.radio_horizon_km,
                    "terrain_blocked": obs.terrain_blocked,
                }
            )
            continue

        if isinstance(obs, RFObservationEvent):
            row = rf_event_to_dataset_row(obs)
            row.update({"aircraft": obs.aircraft_id, "station_id": obs.station_id})
            rows.append(row)
            continue

        if isinstance(obs, dict):
            rows.append(dict(obs))

    return rows


__all__ = ["observations_to_rows"]
