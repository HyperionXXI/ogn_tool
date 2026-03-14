from __future__ import annotations

import json
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np
import pandas as pd

from .analysis_run import resolve_engine_version
from .dataset_summary import build_dataset_summary

if TYPE_CHECKING:
    from ogn_tool.models.analysis_run import AnalysisRun

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

    if isinstance(metric, tuple):
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

    if "analysis_run" in snapshot and not isinstance(snapshot["analysis_run"], dict):
        raise RuntimeError("analysis_run must be a dict when present")


def build_analysis_snapshot(dataset, network, *, run: "AnalysisRun | None" = None) -> dict[str, Any]:
    metrics = dict((network or {}).get("metrics") or {})

    serialized_metrics = {
        name: _serialize_metric(value)
        for name, value in metrics.items()
    }

    snapshot = {
        "snapshot_version": SNAPSHOT_VERSION,
        "engine_version": resolve_engine_version(),
        "created_at": datetime.now(UTC).isoformat(),
        "dataset_summary": build_dataset_summary(dataset),
        "network_metrics": serialized_metrics,
    }

    if run is not None:
        snapshot["analysis_run"] = _serialize_metric(asdict(run))

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
    "build_analysis_snapshot",
    "write_analysis_snapshot",
]
