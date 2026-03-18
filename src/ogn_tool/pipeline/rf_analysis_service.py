"""Service wrappers for RF analysis orchestration."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import pandas as pd

from ogn_tool.config import get_config
from ogn_tool.data.db_repository import (
    create_indexes,
    db_max_ts_epoch,
    db_meta,
    optimize_db,
    rf_sanity_check,
    table_exists_db,
)
from ogn_tool.data.packets_repository import load_packets_window as _load_packets_window
from ogn_tool.data.receptions_repository import load_rf_receptions as _load_rf_receptions
from ogn_tool.engine.rf_engine import RFAnalysisEngine
from ogn_tool.domain.rf_analysis_dataset import RFAnalysisDataset
from ogn_tool.domain.rf_analysis_results import RFAnalysisResults
from ogn_tool.models.rf_observation_vector import RFObservationVector

_LAST_ENGINE: RFAnalysisEngine | None = None


def _filter_packets_for_station(packets_df: pd.DataFrame, station_id: Optional[str]) -> pd.DataFrame:
    if not station_id or packets_df is None or packets_df.empty:
        return packets_df if packets_df is not None else pd.DataFrame()
    if "igate" in packets_df.columns:
        return packets_df[packets_df["igate"].astype(str) == str(station_id)].copy()
    if "receiver" in packets_df.columns:
        return packets_df[packets_df["receiver"].astype(str) == str(station_id)].copy()
    return packets_df


def build_rf_dataset(
    packets_df: pd.DataFrame,
    station_lat: float,
    station_lon: float,
    dataset_mode: str = "STRICT_RF",
    station_id: Optional[str] = None,
) -> dict:
    """Legacy compatibility entrypoint returning the historical dataset dict."""
    global _LAST_ENGINE
    packets_df = _filter_packets_for_station(packets_df, station_id)

    engine = RFAnalysisEngine(packets_df, station_lat, station_lon)
    _LAST_ENGINE = engine
    return engine.build_analysis_dataset(dataset_mode=dataset_mode, station_id=station_id)


def run_rf_analysis(
    packets_df: pd.DataFrame,
    station_lat: float,
    station_lon: float,
    observations: list[RFObservationVector] | None = None,
    station_id: Optional[str] = None,
) -> RFAnalysisResults:
    """Canonical typed service entrypoint for RF analysis."""
    global _LAST_ENGINE
    packets_df = _filter_packets_for_station(packets_df, station_id)

    engine = RFAnalysisEngine(packets_df, station_lat, station_lon)
    _LAST_ENGINE = engine
    dataset = RFAnalysisDataset(observations=observations or [])
    return engine.run(dataset)


def run_rf_diagnostics(dataset_mode: str | None = None, station_id: str | None = None) -> dict:
    return {"dataset_mode": dataset_mode, "station_id": station_id}


def load_packets() -> pd.DataFrame:
    """Load a default packets window for UI pages without explicit filters."""
    cfg = get_config()
    now = datetime.now(timezone.utc)
    since_dt = now - timedelta(hours=6)
    return _load_packets_window(
        db_path=str(cfg.db_path),
        since_iso=since_dt.isoformat().replace("+00:00", "+00:00"),
        since_epoch=int(since_dt.timestamp()),
        dst_types=["OGNFNT", "OGFLR", "OGFLR7", "OGNSDR", "OGNDVS"],
        station_callsign=cfg.station_callsign,
        only_heard_by=True,
        igate_filter="",
        source_mode="Heard-by station",
        qas_filter="",
        limit_rows=25000,
        query_log=None,
    )


def table_exists(db_path: str, table_name: str) -> bool:
    return table_exists_db(db_path, table_name)


def load_packets_window_wrapper(
    db_path: str,
    since_iso: str,
    since_epoch: int,
    dst_types,
    station_callsign: str,
    only_heard_by: bool,
    igate_filter: str,
    source_mode: str,
    qas_filter: str,
    limit_rows: int,
    query_log=None,
):
    return _load_packets_window(
        db_path=db_path,
        since_iso=since_iso,
        since_epoch=since_epoch,
        dst_types=dst_types,
        station_callsign=station_callsign,
        only_heard_by=only_heard_by,
        igate_filter=igate_filter,
        source_mode=source_mode,
        qas_filter=qas_filter,
        limit_rows=limit_rows,
        query_log=query_log,
    )


def load_rf_receptions_wrapper(
    db_path: str,
    since_epoch: int,
    end_epoch: int | None,
    limit_rows: int,
    station_id: str | None = None,
    query_log=None,
):
    return _load_rf_receptions(
        db_path=db_path,
        since_epoch=since_epoch,
        end_epoch=end_epoch,
        limit_rows=limit_rows,
        station_id=station_id,
        query_log=query_log,
    )


# Keep historical public function names.
load_packets_window = load_packets_window_wrapper
load_rf_receptions = load_rf_receptions_wrapper


def run_station_analysis(dataset_mode: str | None = None, station_id: str | None = None) -> dict:
    """Run station-level analysis using the most recently built engine dataset."""
    if _LAST_ENGINE is None:
        return {
            "station_metrics": None,
            "coverage_grid": None,
            "azimuth_histogram": None,
            "directional_balance": None,
        }
    return _LAST_ENGINE.run_station_analysis(
        dataset_mode=dataset_mode,
        station_id=station_id,
    )


def _extract_canonical_network_surface(results) -> dict:
    """Normalize network analysis outputs to the canonical reporting surface."""
    network_metrics = None
    spatial_observations = None

    if isinstance(results, dict):
        network_metrics = results.get("network_metrics")
        spatial_observations = results.get("spatial_observations")
        if network_metrics is None:
            network_metrics = results
    else:
        network_metrics = getattr(results, "network_metrics", None)
        spatial_observations = getattr(results, "spatial_observations", None)

    return {
        "network_metrics": network_metrics,
        "spatial_observations": spatial_observations,
    }


def run_network_analysis(dataset_mode: str | None = None, station_id: str | None = None) -> dict:
    """Run network-level analysis and expose the canonical reporting surface."""
    if _LAST_ENGINE is None:
        return {
            "network_metrics": None,
            "spatial_observations": None,
        }

    results = _LAST_ENGINE.run_from_observations()
    return _extract_canonical_network_surface(results)


__all__ = [
    "build_rf_dataset",
    "run_rf_analysis",
    "run_rf_diagnostics",
    "db_meta",
    "db_max_ts_epoch",
    "optimize_db",
    "create_indexes",
    "rf_sanity_check",
    "load_packets",
    "load_packets_window",
    "load_rf_receptions",
    "run_station_analysis",
    "run_network_analysis",
    "table_exists",
    "get_config",
]
