from dataclasses import dataclass


@dataclass
class StationMetadata:
    """
    Hardware and installation metadata for an OGN groundstation.
    """

    callsign: str
    device_id: str

    board_type: str
    firmware: str
    build_time: str

    latitude: float
    longitude: float
    altitude_m: float

    antenna_environment: str | None = None
    notes: str | None = None
