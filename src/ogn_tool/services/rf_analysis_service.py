"""Service wrappers for RF analysis orchestration."""

from __future__ import annotations

from typing import Optional


import pandas as pd

from ogn_tool.engine.rf_engine import RFAnalysisEngine
from ogn_tool.models.rf_analysis_dataset import RFAnalysisDataset
from ogn_tool.models.rf_analysis_results import RFAnalysisResults
from ogn_tool.models.rf_observation_vector import RFObservationVector
from ogn_tool.services import data_service
from ogn_tool.services.data_service import get_config

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
    return data_service.get_config()


def db_meta(db_path, query_log=None):
    return data_service.db_meta(db_path, query_log=query_log)


def db_max_ts_epoch(db_path):
    return data_service.db_max_ts_epoch(db_path)


def optimize_db(db_path: str, vacuum: bool = False) -> None:
    data_service.optimize_db(db_path, vacuum=vacuum)


def create_indexes(db_path: str) -> None:
    data_service.create_indexes(db_path)


def rf_sanity_check(db_path: str):
    return data_service.rf_sanity_check(db_path)


def load_packets_window(
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
    return data_service.load_packets_window(
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


def load_rf_receptions(
    db_path: str,
    since_epoch: int,
    end_epoch: int | None,
    limit_rows: int,
    station_id: str | None = None,
    query_log=None,
):
    return data_service.load_rf_receptions(
        db_path=db_path,
        since_epoch=since_epoch,
        end_epoch=end_epoch,
        limit_rows=limit_rows,
        station_id=station_id,
        query_log=query_log,
    )


def run_station_analysis(dataset_mode: str | None = None, station_id: str | None = None) -> dict:
    """
    Run station-level analysis using the most recently built engine dataset.
    """
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


def table_exists(db_path: str, table_name: str) -> bool:
    return data_service.table_exists(db_path, table_name)
