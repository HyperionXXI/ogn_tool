from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import math

from ogn_tool.kernel.rf_visibility_model import compute_radio_horizon
from ogn_tool.domain.rf_analysis_dataset import RFAnalysisDataset
from ogn_tool.models.rf_observation_vector import RFObservationVector
from ogn_tool.models.rf_types import RFObservationEvent, packet_to_rf_event
from ogn_tool.rf.geometry import compute_distance_bearing_scalar


def _safe_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(num):
        return None
    return num


def _safe_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        num = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(num):
        return None
    return int(num)


def _altitude_difference(aircraft_alt_m: float | None, station_alt_m: float | None) -> float | None:
    if aircraft_alt_m is None or station_alt_m is None:
        return None
    try:
        return float(aircraft_alt_m) - float(station_alt_m)
    except (TypeError, ValueError):
        return None


class _SpatialIndex:
    def __init__(self, station_coords: Dict[str, tuple[float, float, float | None]], grid_size: float = 0.05):
        self.station_coords = station_coords
        self.grid_size = max(1e-6, float(grid_size))
        self._cache: Dict[tuple[str, int, int], tuple[float, float]] = {}

    def _cell(self, lat: float, lon: float) -> tuple[int, int]:
        return int(math.floor(float(lat) / self.grid_size)), int(math.floor(float(lon) / self.grid_size))

    def _center(self, c_lat: int, c_lon: int) -> tuple[float, float]:
        return (float(c_lat) + 0.5) * self.grid_size, (float(c_lon) + 0.5) * self.grid_size

    def get_distance_bearing(self, station_id: str, lat: float, lon: float) -> tuple[float | None, float | None]:
        coords = self.station_coords.get(str(station_id))
        if coords is None:
            return None, None
        c_lat, c_lon = self._cell(lat, lon)
        key = (str(station_id), c_lat, c_lon)
        if key not in self._cache:
            st_lat, st_lon, _ = coords
            center_lat, center_lon = self._center(c_lat, c_lon)
            self._cache[key] = compute_distance_bearing_scalar(st_lat, st_lon, center_lat, center_lon)
        d, b = self._cache[key]
        return float(d), float(b)


def _extract_aircraft_id(packet: Dict[str, Any]) -> str | None:
    aircraft = packet.get("aircraft_id")
    if aircraft is None:
        aircraft = packet.get("src")
    if aircraft is None:
        aircraft = packet.get("aircraft")
    if aircraft is None:
        return None
    return str(aircraft)


def _extract_timestamp(packet: Dict[str, Any]) -> int | None:
    ts = packet.get("timestamp")
    if ts is None:
        ts = packet.get("ts_epoch")
    if ts is None:
        return None
    return _safe_int(ts)


@dataclass
class AircraftState:
    aircraft_id: str
    timestamp: int
    lat: float
    lon: float
    altitude: float | None = None


@dataclass
class IncrementalMetrics:
    packet_count: int = 0
    station_packet_count: Dict[str, int] = field(default_factory=dict)
    station_max_range_km: Dict[str, float] = field(default_factory=dict)
    station_coverage_cells: Dict[str, set[tuple[float, float]]] = field(default_factory=dict)
    station_azimuth_histogram: Dict[str, list[int]] = field(default_factory=dict)
    shadow_sectors: Dict[str, list[int]] = field(default_factory=dict)


class RFStateEngine:
    """Incremental RF state engine for streaming packet analysis.

    This component is a streaming adapter. The canonical analysis kernel remains
    batch/snapshot oriented. Use `snapshot()` to materialize a compatible
    `RFAnalysisDataset` for the batch engine.
    """

    def __init__(
        self,
        station_coords: Optional[Dict[str, tuple[float, float, float | None]]] = None,
        grid_cell_deg: float = 0.05,
        azimuth_bins: int = 36,
        ttl_seconds: int = 3600,
        cleanup_interval_packets: int = 256,
    ) -> None:
        self.station_coords = station_coords or {}
        self.grid_cell_deg = float(grid_cell_deg)
        self.azimuth_bins = int(azimuth_bins)
        self.ttl_seconds = int(ttl_seconds)
        self.cleanup_interval_packets = max(1, int(cleanup_interval_packets))

        self.aircraft_states: Dict[str, AircraftState] = {}
        self.metrics = IncrementalMetrics()
        self._ingest_counter = 0
        self._observation_vectors: list[RFObservationVector] = []
        self.spatial_index = _SpatialIndex(self.station_coords, self.grid_cell_deg)

    def cleanup_states(self, current_timestamp: int | None = None) -> int:
        if not self.aircraft_states:
            return 0

        if current_timestamp is None:
            current_timestamp = max((s.timestamp for s in self.aircraft_states.values()), default=0)

        to_delete = [aid for aid, st in self.aircraft_states.items() if current_timestamp - st.timestamp > self.ttl_seconds]
        for aid in to_delete:
            self.aircraft_states.pop(aid, None)
        return len(to_delete)

    def update_aircraft_state(self, packet: Dict[str, Any]) -> AircraftState | None:
        aircraft_id = _extract_aircraft_id(packet)
        timestamp = _extract_timestamp(packet)
        lat = _safe_float(packet.get("lat"))
        lon = _safe_float(packet.get("lon"))
        altitude = _safe_float(packet.get("altitude"))
        if altitude is None:
            altitude = _safe_float(packet.get("altitude_m"))
        if altitude is None:
            altitude = _safe_float(packet.get("alt"))

        if aircraft_id is None or timestamp is None or lat is None or lon is None:
            return None

        state = AircraftState(aircraft_id=aircraft_id, timestamp=timestamp, lat=lat, lon=lon, altitude=altitude)
        self.aircraft_states[aircraft_id] = state
        return state

    def build_rf_observation(self, packet: Dict[str, Any]) -> RFObservationEvent | None:
        event = packet_to_rf_event(packet)
        if event.station_id is None or event.aircraft_id is None or event.timestamp is None:
            return None

        state = self.aircraft_states.get(event.aircraft_id)
        if state is None:
            state = self.update_aircraft_state(packet)
            if state is None:
                return None

        st_coords = self.station_coords.get(event.station_id)
        if st_coords is not None:
            _st_lat, _st_lon, st_alt = st_coords
            distance, bearing = self.spatial_index.get_distance_bearing(event.station_id, state.lat, state.lon)
            event.distance = distance
            event.bearing = bearing
            event.altitude_difference = _altitude_difference(state.altitude, st_alt)

        if event.distance is None:
            event.distance = _safe_float(packet.get("distance"))
        if event.distance is None:
            event.distance = _safe_float(packet.get("distance_km"))

        if event.bearing is None:
            event.bearing = _safe_float(packet.get("bearing"))
        if event.bearing is None:
            event.bearing = _safe_float(packet.get("bearing_deg"))

        if event.altitude_difference is None:
            event.altitude_difference = _safe_float(packet.get("altitude_difference"))
        if event.altitude_difference is None:
            event.altitude_difference = _safe_float(packet.get("relative_alt_m"))

        if packet.get("ts_ns") is not None:
            metadata = dict(event.metadata or {})
            metadata["ts_ns"] = packet.get("ts_ns")
            event.metadata = metadata

        return event

    def _event_to_vector(self, obs: RFObservationEvent, state: AircraftState | None) -> RFObservationVector | None:
        if obs.station_id is None or obs.aircraft_id is None or obs.timestamp is None:
            return None

        lat = obs.lat if obs.lat is not None else getattr(state, "lat", None)
        lon = obs.lon if obs.lon is not None else getattr(state, "lon", None)
        altitude = obs.altitude if obs.altitude is not None else getattr(state, "altitude", None)
        distance = obs.distance
        bearing = obs.bearing

        if lat is None or lon is None or altitude is None or distance is None or bearing is None:
            return None

        station_alt = None
        if obs.station_id in self.station_coords:
            _st_lat, _st_lon, station_alt = self.station_coords[obs.station_id]
        horizon = compute_radio_horizon(station_alt or 0.0, altitude).get("radio_horizon_km", 0.0)

        metadata = obs.metadata or {}
        timestamp_ns = _safe_int(metadata.get("ts_ns")) if metadata else None

        return RFObservationVector(
            station_id=str(obs.station_id),
            aircraft_id=str(obs.aircraft_id),
            lat=float(lat),
            lon=float(lon),
            altitude_m=float(altitude),
            distance_km=float(distance),
            bearing_deg=float(bearing),
            radio_horizon_km=float(horizon),
            timestamp=int(obs.timestamp),
            timestamp_ns=timestamp_ns,
        )

    def _update_incremental_metrics(self, obs: RFObservationEvent, state: AircraftState | None) -> None:
        self.metrics.packet_count += 1
        st = obs.station_id
        if st is None:
            return

        self.metrics.station_packet_count[st] = self.metrics.station_packet_count.get(st, 0) + 1

        if obs.distance is not None:
            cur = self.metrics.station_max_range_km.get(st)
            if cur is None or obs.distance > cur:
                self.metrics.station_max_range_km[st] = obs.distance

        if state is not None:
            cell = (
                round(float(state.lat) / self.grid_cell_deg) * self.grid_cell_deg,
                round(float(state.lon) / self.grid_cell_deg) * self.grid_cell_deg,
            )
            self.metrics.station_coverage_cells.setdefault(st, set()).add(cell)

        if obs.bearing is not None:
            hist = self.metrics.station_azimuth_histogram.setdefault(st, [0] * self.azimuth_bins)
            b = float(obs.bearing) % 360.0
            idx = min(self.azimuth_bins - 1, int(math.floor((b / 360.0) * self.azimuth_bins)))
            hist[idx] += 1

            nonzero = [v for v in hist if v > 0]
            if nonzero:
                mean = sum(hist) / len(hist)
                flagged = [i for i, v in enumerate(hist) if v > 0 and v < 0.25 * mean]
            else:
                flagged = []
            self.metrics.shadow_sectors[st] = flagged

    def ingest_packet(self, packet: Dict[str, Any]) -> RFObservationEvent | None:
        state = self.update_aircraft_state(packet)
        obs = self.build_rf_observation(packet)
        if obs is None:
            return None

        self._update_incremental_metrics(obs, state)

        vector = self._event_to_vector(obs, state)
        if vector is not None:
            self._observation_vectors.append(vector)

        self._ingest_counter += 1
        if self._ingest_counter % self.cleanup_interval_packets == 0 and obs.timestamp is not None:
            self.cleanup_states(current_timestamp=obs.timestamp)

        return obs

    def snapshot(self) -> RFAnalysisDataset:
        """Materialize a batch-compatible snapshot dataset from the current stream state."""
        return RFAnalysisDataset(observations=list(self._observation_vectors))

    def get_metrics_snapshot(self) -> Dict[str, Any]:
        coverage_cells_count = {st: len(cells) for st, cells in self.metrics.station_coverage_cells.items()}
        return {
            "packet_count": self.metrics.packet_count,
            "station_packet_count": dict(self.metrics.station_packet_count),
            "station_max_range_km": dict(self.metrics.station_max_range_km),
            "station_coverage_cells": coverage_cells_count,
            "station_azimuth_histogram": dict(self.metrics.station_azimuth_histogram),
            "shadow_sectors": dict(self.metrics.shadow_sectors),
        }


__all__ = ["AircraftState", "RFObservationEvent", "IncrementalMetrics", "RFStateEngine"]

