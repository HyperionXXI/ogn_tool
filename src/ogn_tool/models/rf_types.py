from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass
class RFObservationEvent:
    """Canonical RF observation event contract.

    This type represents one station reception of one aircraft state and is
    intended to be the shared RF data contract across analysis and engine layers.
    """

    station_id: str | None
    aircraft_id: str | None
    timestamp: int | None

    distance: float | None = None
    bearing: float | None = None
    altitude_difference: float | None = None

    snr: float | None = None
    freq_offset: float | None = None
    bit_errors: int | None = None

    lat: float | None = None
    lon: float | None = None
    altitude: float | None = None

    metadata: dict[str, Any] | None = None


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    if out != out:  # NaN
        return None
    return out


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def packet_to_rf_event(packet: Mapping[str, Any]) -> RFObservationEvent:
    """Convert a packet-like row to canonical RFObservationEvent."""
    station_id = packet.get("station_id") or packet.get("receiver") or packet.get("igate")
    aircraft_id = packet.get("aircraft_id") or packet.get("src") or packet.get("aircraft")
    timestamp = _safe_int(packet.get("timestamp") if packet.get("timestamp") is not None else packet.get("ts_epoch"))

    return RFObservationEvent(
        station_id=str(station_id) if station_id is not None else None,
        aircraft_id=str(aircraft_id) if aircraft_id is not None else None,
        timestamp=timestamp,
        distance=_safe_float(packet.get("distance") if packet.get("distance") is not None else packet.get("distance_km")),
        bearing=_safe_float(packet.get("bearing") if packet.get("bearing") is not None else packet.get("bearing_deg")),
        altitude_difference=_safe_float(
            packet.get("altitude_difference")
            if packet.get("altitude_difference") is not None
            else packet.get("relative_alt_m")
        ),
        snr=_safe_float(packet.get("snr") if packet.get("snr") is not None else packet.get("snr_db")),
        freq_offset=_safe_float(packet.get("freq_offset")),
        bit_errors=_safe_int(packet.get("bit_errors")),
        lat=_safe_float(packet.get("lat")),
        lon=_safe_float(packet.get("lon")),
        altitude=_safe_float(
            packet.get("altitude")
            if packet.get("altitude") is not None
            else packet.get("altitude_m")
        ),
        metadata={
            k: packet.get(k)
            for k in ["_row_id", "raw", "qas", "dst", "ts_utc", "packet_id", "id"]
            if k in packet
        }
        or None,
    )


def state_to_rf_event(state: Mapping[str, Any], reception: Mapping[str, Any] | None = None) -> RFObservationEvent:
    """Build canonical RFObservationEvent from aircraft state (+ optional reception)."""
    reception = reception or {}
    merged = {**state, **reception}
    return packet_to_rf_event(merged)


def rf_event_to_dataset_row(event: RFObservationEvent) -> dict[str, Any]:
    """Convert canonical RFObservationEvent to dataset row with legacy aliases."""
    row = {
        "station_id": event.station_id,
        "aircraft_id": event.aircraft_id,
        "timestamp": event.timestamp,
        "distance": event.distance,
        "bearing": event.bearing,
        "altitude_difference": event.altitude_difference,
        "snr": event.snr,
        "freq_offset": event.freq_offset,
        "bit_errors": event.bit_errors,
        "lat": event.lat,
        "lon": event.lon,
        "altitude": event.altitude,
        # compatibility aliases used in existing engine/analysis code
        "igate": event.station_id,
        "src": event.aircraft_id,
        "ts_epoch": event.timestamp,
        "distance_km": event.distance,
        "bearing_deg": event.bearing,
        "relative_alt_m": event.altitude_difference,
    }
    if event.metadata:
        row.update(event.metadata)
    return row


__all__ = [
    "RFObservationEvent",
    "packet_to_rf_event",
    "state_to_rf_event",
    "rf_event_to_dataset_row",
]