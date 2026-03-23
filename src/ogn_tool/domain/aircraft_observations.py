from __future__ import annotations

from statistics import median
from typing import Any, Iterable, Mapping


def _to_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


def _to_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    from math import asin, cos, radians, sin, sqrt

    r = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    return 2 * r * asin(sqrt(a))


def build_aircraft_observations(
    packets: Iterable[Mapping[str, Any]],
    temporal_threshold_s: int = 10,
    max_cluster_radius_km: float = 20.0,
) -> list[dict[str, Any]]:
    """Build canonical aircraft observations from packet-level records.

    Required packet fields: src, lat, lon, ts_epoch, igate.
    """
    normalized: list[dict[str, Any]] = []
    for row in packets:
        if not isinstance(row, Mapping):
            continue

        aircraft_id = row.get("src") or row.get("aircraft_id")
        lat = _to_float(row.get("lat"))
        lon = _to_float(row.get("lon"))
        ts_epoch = _to_int(row.get("ts_epoch"))
        station = row.get("igate") or row.get("station_id")

        if not aircraft_id or lat is None or lon is None or ts_epoch is None:
            continue

        normalized.append(
            {
                "aircraft_id": str(aircraft_id),
                "lat": lat,
                "lon": lon,
                "ts_epoch": ts_epoch,
                "station_id": str(station).strip() if station else "",
            }
        )

    if not normalized:
        return []

    normalized.sort(key=lambda r: (r["aircraft_id"], r["ts_epoch"]))

    observations: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    def flush(cluster: dict[str, Any] | None) -> None:
        if not cluster:
            return
        seen_by = sorted(s for s in cluster["seen_by"] if s)
        obs = {
            "aircraft_id": cluster["aircraft_id"],
            "lat": float(median(cluster["lats"])),
            "lon": float(median(cluster["lons"])),
            "timestamp_epoch": int(median(cluster["times"])),
            "seen_by": seen_by,
        }
        observations.append(obs)

    for row in normalized:
        if current is None:
            current = {
                "aircraft_id": row["aircraft_id"],
                "lats": [row["lat"]],
                "lons": [row["lon"]],
                "times": [row["ts_epoch"]],
                "seen_by": {row["station_id"]} if row["station_id"] else set(),
            }
            continue

        same_aircraft = row["aircraft_id"] == current["aircraft_id"]
        dt = row["ts_epoch"] - current["times"][-1]
        center_lat = float(median(current["lats"]))
        center_lon = float(median(current["lons"]))
        spatial_km = _haversine_km(center_lat, center_lon, row["lat"], row["lon"])

        if same_aircraft and dt <= temporal_threshold_s and spatial_km <= max_cluster_radius_km:
            current["lats"].append(row["lat"])
            current["lons"].append(row["lon"])
            current["times"].append(row["ts_epoch"])
            if row["station_id"]:
                current["seen_by"].add(row["station_id"])
            continue

        flush(current)
        current = {
            "aircraft_id": row["aircraft_id"],
            "lats": [row["lat"]],
            "lons": [row["lon"]],
            "times": [row["ts_epoch"]],
            "seen_by": {row["station_id"]} if row["station_id"] else set(),
        }

    flush(current)
    return observations


def project_aircraft_positions(observations: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    projected: list[dict[str, Any]] = []
    for obs in observations:
        if not isinstance(obs, Mapping):
            continue

        aircraft_id = obs.get("aircraft_id")
        lat = _to_float(obs.get("lat"))
        lon = _to_float(obs.get("lon"))
        ts_epoch = _to_int(obs.get("timestamp_epoch"))
        seen_by = obs.get("seen_by")

        if not aircraft_id or lat is None or lon is None:
            continue

        projected.append(
            {
                "src": str(aircraft_id),
                "lat": lat,
                "lon": lon,
                "timestamp_epoch": ts_epoch,
                "seen_by": list(seen_by) if isinstance(seen_by, (list, tuple, set)) else [],
            }
        )

    return projected


__all__ = ["build_aircraft_observations", "project_aircraft_positions"]

