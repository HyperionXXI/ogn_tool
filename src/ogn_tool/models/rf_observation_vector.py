from dataclasses import dataclass


@dataclass
class RFObservationVector:
    station_id: str
    aircraft_id: str

    lat: float
    lon: float
    altitude_m: float

    distance_km: float
    bearing_deg: float

    radio_horizon_km: float
    terrain_blocked: bool | None = None
    timestamp: int | None = None
    timestamp_ns: int | None = None
