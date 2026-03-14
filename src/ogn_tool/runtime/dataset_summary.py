from __future__ import annotations

from typing import Any

import pandas as pd


def _serialize_summary_value(value: Any) -> Any:
    if value is pd.NA:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    if isinstance(value, pd.Timestamp):
        return value.isoformat()

    return value


def build_dataset_summary(dataset) -> dict[str, Any]:
    observations = getattr(dataset, "observations", None)

    observation_count = 0
    station_count: int | None = None
    aircraft_count: int | None = None
    time_min: Any = None
    time_max: Any = None

    if observations is None:
        observation_count = 0
    elif isinstance(observations, pd.DataFrame):
        frame = observations.copy()
        observation_count = len(frame)

        if "station_id" in frame.columns:
            station_count = int(frame["station_id"].dropna().nunique())
        elif "igate" in frame.columns:
            station_count = int(frame["igate"].dropna().nunique())

        if "aircraft" in frame.columns:
            aircraft_count = int(frame["aircraft"].dropna().nunique())
        elif "src" in frame.columns:
            aircraft_count = int(frame["src"].dropna().nunique())
        elif "aircraft_id" in frame.columns:
            aircraft_count = int(frame["aircraft_id"].dropna().nunique())

        if "ts_epoch" in frame.columns:
            time_min = frame["ts_epoch"].min()
            time_max = frame["ts_epoch"].max()
        elif "timestamp" in frame.columns:
            time_min = frame["timestamp"].min()
            time_max = frame["timestamp"].max()
    elif isinstance(observations, (list, tuple)):
        observation_count = len(observations)
        station_ids = {
            getattr(obs, "station_id", None)
            for obs in observations
            if getattr(obs, "station_id", None)
        }
        aircraft_ids = {
            getattr(obs, "aircraft_id", None)
            for obs in observations
            if getattr(obs, "aircraft_id", None)
        }
        timestamps = [
            getattr(obs, "timestamp", None)
            for obs in observations
            if getattr(obs, "timestamp", None) is not None
        ]
        station_count = len(station_ids)
        aircraft_count = len(aircraft_ids)
        if timestamps:
            time_min = min(timestamps)
            time_max = max(timestamps)

    return {
        "observation_count": observation_count,
        "station_count": station_count,
        "aircraft_count": aircraft_count,
        "time_min": _serialize_summary_value(time_min),
        "time_max": _serialize_summary_value(time_max),
    }


__all__ = ["build_dataset_summary"]
