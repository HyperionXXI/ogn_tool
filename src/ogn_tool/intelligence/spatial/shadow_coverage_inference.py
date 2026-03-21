from __future__ import annotations

import math
from math import atan2, degrees, floor, log, radians
from typing import Dict

import pandas as pd


REQUIRED_STATION_COL = "station_id"



def compute_station_angular_entropy(
    observations: pd.DataFrame,
    *,
    sector_count: int = 16,
) -> Dict[str, float]:
    if not isinstance(observations, pd.DataFrame):
        raise ValueError("observations must be a pandas DataFrame")
    if sector_count < 2:
        raise ValueError("sector_count must be >= 2")
    if REQUIRED_STATION_COL not in observations.columns:
        raise ValueError("observations must contain station_id")

    bearings = _resolve_bearings(observations)
    sector_size = 360.0 / sector_count
    entropy_by_station: Dict[str, float] = {}

    for station_id, group in bearings.groupby("station_id"):
        counts = [0] * sector_count

        for bearing in group["bearing_deg"]:
            sector = int(floor(bearing / sector_size)) % sector_count
            counts[sector] += 1

        total = sum(counts)
        if total == 0:
            entropy_by_station[str(station_id)] = 0.0
            continue

        entropy = 0.0
        for count in counts:
            if count == 0:
                continue
            probability = count / total
            entropy -= probability * log(probability)

        entropy_norm = entropy / log(sector_count)
        entropy_by_station[str(station_id)] = float(max(0.0, min(1.0, entropy_norm)))

    return entropy_by_station



def compute_shadow_risk_scores(
    observations: pd.DataFrame,
    *,
    sector_count: int = 16,
) -> Dict[str, float]:
    entropy = compute_station_angular_entropy(
        observations,
        sector_count=sector_count,
    )
    return {station_id: 1.0 - value for station_id, value in entropy.items()}



def _resolve_bearings(observations: pd.DataFrame) -> pd.DataFrame:
    if "bearing_deg" in observations.columns:
        work = observations[["station_id", "bearing_deg"]].copy()
        work["bearing_deg"] = pd.to_numeric(work["bearing_deg"], errors="coerce")
        work = work.dropna(subset=["bearing_deg"])
        work["bearing_deg"] = work["bearing_deg"] % 360.0
        return work

    required = {"lat", "lon", "station_lat", "station_lon"}
    if not required.issubset(observations.columns):
        raise ValueError(
            "observations must contain bearing_deg or lat/lon + station_lat/station_lon"
        )

    work = observations[["station_id", "lat", "lon", "station_lat", "station_lon"]].copy()
    for column in ["lat", "lon", "station_lat", "station_lon"]:
        work[column] = pd.to_numeric(work[column], errors="coerce")
    work = work.dropna()

    bearings = []
    for row in work.itertuples(index=False):
        bearings.append(_bearing(row.station_lat, row.station_lon, row.lat, row.lon))

    return pd.DataFrame(
        {
            "station_id": work["station_id"].astype(str).values,
            "bearing_deg": bearings,
        }
    )



def _bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1 = radians(lat1)
    lat2 = radians(lat2)
    dlon = radians(lon2 - lon1)

    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - (
        math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    )

    bearing = degrees(atan2(y, x))
    return (bearing + 360.0) % 360.0


__all__ = ["compute_station_angular_entropy", "compute_shadow_risk_scores"]
