from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

try:
    from ogn_tool import __version__ as ENGINE_VERSION
except Exception:
    ENGINE_VERSION = "1.1"

SNAPSHOT_VERSION = "1"

REQUIRED_SNAPSHOT_KEYS = {
    "snapshot_version",
    "engine_version",
    "created_at",
    "dataset_summary",
    "network_metrics",
}


def _serialize_value(value: Any) -> Any:
    """Convert scalar values to a JSON-safe representation."""
    if value is pd.NA:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()

    if isinstance(value, np.generic):
        return value.item()

    return value


def _serialize_record(record: dict[str, Any]) -> dict[str, Any]:
    return {key: _serialize_value(value) for key, value in record.items()}


def _serialize_metric(metric: Any) -> Any:
    if isinstance(metric, pd.DataFrame):
        return [_serialize_record(record) for record in metric.to_dict(orient="records")]

    if isinstance(metric, dict):
        return {key: _serialize_metric(value) for key, value in metric.items()}

    if isinstance(metric, list):
        return [_serialize_metric(value) for value in metric]

    return _serialize_value(metric)


def _validate_snapshot_structure(snapshot: dict[str, Any]) -> None:
    missing = REQUIRED_SNAPSHOT_KEYS - set(snapshot.keys())
    if missing:
        raise RuntimeError(
            f"Invalid snapshot structure, missing keys: {sorted(missing)}"
        )

    if not isinstance(snapshot["dataset_summary"], dict):
        raise RuntimeError("dataset_summary must be a dict")

    if not isinstance(snapshot["network_metrics"], dict):
        raise RuntimeError("network_metrics must be a dict")


def _dataset_summary(dataset) -> dict[str, Any]:
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
        "time_min": _serialize_value(time_min),
        "time_max": _serialize_value(time_max),
    }


def build_analysis_snapshot(dataset, network) -> dict[str, Any]:
    metrics = dict((network or {}).get("metrics") or {})

    serialized_metrics = {
        name: _serialize_metric(value)
        for name, value in metrics.items()
    }

    snapshot = {
        "snapshot_version": SNAPSHOT_VERSION,
        "engine_version": ENGINE_VERSION,
        "created_at": datetime.now(UTC).isoformat(),
        "dataset_summary": _dataset_summary(dataset),
        "network_metrics": serialized_metrics,
    }

    _validate_snapshot_structure(snapshot)
    return snapshot


def write_analysis_snapshot(snapshot: dict[str, Any], path: str) -> None:
    destination = Path(path)
    destination.write_text(
        json.dumps(snapshot, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


__all__ = [
    "SNAPSHOT_VERSION",
    "ENGINE_VERSION",
    "build_analysis_snapshot",
    "write_analysis_snapshot",
]
