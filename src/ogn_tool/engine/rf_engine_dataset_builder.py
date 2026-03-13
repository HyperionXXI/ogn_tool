from __future__ import annotations

from typing import Any, Dict, Iterable, List

import pandas as pd

from ogn_tool.analysis.rf_dataset_builder import build_rf_dataset
from ogn_tool.rf import azimuth as analysis_azimuth
from ogn_tool.analysis.network import station_range as analysis_station_range
from ogn_tool.analysis.network import station_quality as analysis_station_quality
from ogn_tool.analysis.geo import compute_distance_bearing
from ogn_tool.analysis.network_metrics import (
    build_network_metrics,
    build_station_metrics,
    detect_network_blind_zones,
    enrich_coverage_grid,
)
from ogn_tool.analysis.rf_diagnosis import RFDiagnosis
from ogn_tool.analysis.rf_observations import compute_distance, compute_bearing
from ogn_tool.engine.rf_dataset_builder import build_observations
from ogn_tool.analysis.rf_metrics.directional_analysis import build_directional_diagnostics
from ogn_tool.analysis.rf_metrics.probability_field import build_rf_probability_field
from ogn_tool.analysis.rf_metrics.rf_statistics import summarize_signal_quality
from ogn_tool.analysis.normalization.observation_builder import build_observations as build_observation_payload
from ogn_tool.engine.rf_model_runner import run
from ogn_tool.engine.rf_models_registry import MODELS
from ogn_tool.analysis.normalization.observation_rows import observations_to_rows
from ogn_tool.engine.rf_engine_network import (
    build_radio_events,
    build_station_reception,
    compute_coverage_redundancy,
    compute_blind_zones,
    compute_station_overlap,
)


def build_analysis_dataset_impl(engine: Any, dataset_mode: str = "NETWORK", station_id: str | None = None) -> dict:
    packets_input = engine.packets.copy()
    if "receiver" in packets_input.columns and "igate" not in packets_input.columns:
        packets_input["igate"] = packets_input["receiver"]
    packets_input = packets_input.reset_index(drop=False).rename(columns={"index": "_row_id"})

    packet_rows = packets_input.to_dict("records")
    observations = build_observations(packet_rows)
    rows = observations_to_rows(observations)
    observations_df = pd.DataFrame(rows)

    if observations_df.empty:
        packets_all = packets_input.copy()
    else:
        if "_row_id" not in observations_df.columns:
            observations_df["_row_id"] = pd.Series(dtype="Int64")

        meta_cols = [
            c
            for c in ["_row_id", "raw", "qas", "dst", "ts_utc", "receiver", "packet_id", "id"]
            if c in packets_input.columns
        ]
        meta_df = packets_input[meta_cols].copy() if meta_cols else pd.DataFrame()
        if not meta_df.empty and "_row_id" in meta_df.columns:
            packets_all = observations_df.merge(meta_df, on="_row_id", how="left")
        else:
            packets_all = observations_df.copy()

        if "aircraft" in packets_all.columns and "src" not in packets_all.columns:
            packets_all["src"] = packets_all["aircraft"]
        if "station_id" in packets_all.columns and "igate" not in packets_all.columns:
            packets_all["igate"] = packets_all["station_id"]
        if "timestamp" in packets_all.columns and "ts_epoch" not in packets_all.columns:
            packets_all["ts_epoch"] = pd.to_numeric(packets_all["timestamp"], errors="coerce").astype("Int64")

    packets_filtered = packets_all
    packets_rf = packets_all.iloc[0:0].copy()
    dataset_mode = (dataset_mode or "NETWORK").upper()

    if dataset_mode == "NETWORK":
        packets_rf = packets_all
        packets_filtered = packets_all
    elif dataset_mode == "STATION_RF":
        if "igate" in packets_all.columns and station_id:
            packets_rf = packets_all[packets_all["igate"].astype(str) == station_id].copy()
        else:
            packets_rf = packets_all.iloc[0:0].copy()
        packets_filtered = packets_rf
    else:
        if "qas" in packets_all.columns:
            qas_upper = packets_all["qas"].astype(str).str.upper()
            packets_rf = packets_all[qas_upper.isin(["QAR", "QAO"])].copy()
        packets_filtered = packets_rf

    if "receiver" in packets_rf.columns:
        packets_rf["distance_km"] = compute_distance(packets_rf, engine.station_lat, engine.station_lon)
        packets_rf["bearing_deg"] = compute_bearing(packets_rf, engine.station_lat, engine.station_lon)
    elif "lat" in packets_rf.columns and "lon" in packets_rf.columns:
        lat = packets_rf["lat"].to_numpy()
        lon = packets_rf["lon"].to_numpy()

        distance_km, bearing_deg = compute_distance_bearing(
            lat,
            lon,
            station_lat=engine.station_lat,
            station_lon=engine.station_lon,
        )

        packets_rf["distance_km"] = distance_km
        packets_rf["bearing_deg"] = bearing_deg

    if "distance_km" in packets_filtered.columns:
        packets_filtered["station_range_km"] = packets_filtered["distance_km"]

    if "altitude" in packets_filtered.columns and "altitude_m" not in packets_filtered.columns:
        packets_filtered["altitude_m"] = pd.to_numeric(packets_filtered["altitude"], errors="coerce")

    directional = build_directional_diagnostics(
        packets_rf=packets_rf,
        packets_filtered=packets_filtered,
        station_lat=engine.station_lat,
        station_lon=engine.station_lon,
    )
    azimuth_histogram = directional.get("azimuth_histogram")
    directional_balance = directional.get("directional_balance")

    rf_issues = []
    rf_health = "UNKNOWN"

    stations = []
    if not packets_filtered.empty and "igate" in packets_filtered.columns:
        stations = sorted(packets_filtered["igate"].astype(str).dropna().unique().tolist())

    distance_df, _grid = build_rf_dataset(packets_filtered, engine.station_lat, engine.station_lon)
    coverage_grid = build_rf_probability_field(distance_df)
    shadow_map = directional.get("shadow_map")

    coverage_grid = enrich_coverage_grid(distance_df, coverage_grid)

    radio_events = build_radio_events(packets_filtered)
    station_reception = build_station_reception(packets_filtered)
    coverage_redundancy_grid = compute_coverage_redundancy(radio_events, station_reception)
    blind_cells = compute_blind_zones(coverage_redundancy_grid)
    station_overlap_matrix = compute_station_overlap(station_reception)

    network_blind_zones = detect_network_blind_zones(coverage_redundancy_grid)

    station_metrics = build_station_metrics(distance_df, coverage_grid)
    network_metrics = build_network_metrics(
        coverage_grid=coverage_grid,
        coverage_redundancy_grid=coverage_redundancy_grid,
        blind_cells=blind_cells,
        station_metrics=station_metrics,
    )

    metrics: dict[str, Any] = {
        "p95_range_km": station_metrics["p95_distance"].max() if not station_metrics.empty else None,
        "max_range_km": station_metrics["max_distance"].max() if not station_metrics.empty else None,
        "coverage_cells": network_metrics.get("coverage_cells"),
        "redundancy_cells": network_metrics.get("redundancy_cells"),
        "network_resilience_score": network_metrics.get("network_resilience_score"),
    }

    metrics.update(summarize_signal_quality(packets_filtered))

    rf_diagnosis = RFDiagnosis(metrics, directional_balance)
    rf_issues = rf_diagnosis.evaluate()
    rf_health = rf_diagnosis.health_score()

    dataset = {
        "observations": observations_df,
        "packets_all": packets_all,
        "packets_rf": packets_rf,
        "packets_filtered": packets_filtered,
        "rf_receptions": packets_filtered,
        "radio_events": radio_events,
        "station_reception": station_reception,
        "coverage_grid": coverage_grid,
        "coverage_redundancy_grid": coverage_redundancy_grid,
        "station_metrics": station_metrics,
        "network_metrics": network_metrics,
        "azimuth_histogram": azimuth_histogram,
        "directional_balance": directional_balance,
        "rf_diagnosis": {
            "health": rf_health,
            "issues": rf_issues,
        },
        "shadow_map": shadow_map,
        "station_overlap_matrix": station_overlap_matrix,
        "blind_cells": blind_cells,
        "network_blind_zones": network_blind_zones,
        "stations": stations,
        "dataset_mode": dataset_mode,
    }
    engine._last_dataset = dataset
    engine._last_dataset_mode = dataset_mode
    engine._last_station_id = station_id
    return dataset


def build_observations_impl(engine: Any) -> tuple[pd.DataFrame, pd.DataFrame]:
    distance_df, grid = build_rf_dataset(engine.packets, engine.station_lat, engine.station_lon)

    grid_for_analysis = grid.copy()
    if "packets" in grid_for_analysis.columns:
        grid_for_analysis["packet_count"] = grid_for_analysis["packets"]
    if "max_distance" in grid_for_analysis.columns:
        grid_for_analysis["max_distance_km"] = grid_for_analysis["max_distance"]
    if "grid_lat" in grid_for_analysis.columns:
        grid_for_analysis["lat"] = grid_for_analysis["grid_lat"]
    if "grid_lon" in grid_for_analysis.columns:
        grid_for_analysis["lon"] = grid_for_analysis["grid_lon"]
    if "best_rssi_db" not in grid_for_analysis.columns:
        grid_for_analysis["best_rssi_db"] = pd.NA

    return distance_df, grid_for_analysis


def compute_metrics_impl(
    engine: Any,
    distance_df: pd.DataFrame,
    grid_for_analysis: pd.DataFrame,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    range_stats = analysis_station_range.analyze(grid_for_analysis)
    quality_stats = analysis_station_quality.analyze(grid_for_analysis)
    signal_stats = run(MODELS["signal_distance"], df_observations=distance_df, station_lat=engine.station_lat, station_lon=engine.station_lon)
    altitude_stats = run(MODELS["altitude_distance"], df_observations=distance_df, station_lat=engine.station_lat, station_lon=engine.station_lon)
    horizon_stats = run(MODELS["radio_horizon"], df_observations=distance_df, station_lat=engine.station_lat, station_lon=engine.station_lon)
    terrain_stats = run(MODELS["terrain"], df_grid=grid_for_analysis, station_lat=engine.station_lat, station_lon=engine.station_lon)
    visibility_stats = run(MODELS["terrain_visibility"], df_observations=distance_df, station_lat=engine.station_lat, station_lon=engine.station_lon)

    metrics: Dict[str, Any] = {
        "station_range": range_stats,
        "station_quality": quality_stats,
        "signal_distance": signal_stats,
        "altitude_distance": altitude_stats,
        "radio_horizon": horizon_stats,
        "terrain": terrain_stats,
        "terrain_visibility": visibility_stats,
    }

    summary = range_stats.get("summary") or {}
    metrics.update(
        {
            "p95_range_km": summary.get("p95_distance_km"),
            "max_range_km": summary.get("max_distance_km"),
            "rf_packets": int(len(distance_df)),
            "health": (quality_stats.get("summary") or {}).get("quality_score"),
            "grid_base": grid_for_analysis,
        }
    )

    return metrics, terrain_stats


def run_rf_models_impl(engine: Any, distance_df: pd.DataFrame) -> Dict[str, Any]:
    azimuth_df = analysis_azimuth.compute_azimuth_radiation(distance_df, engine.station_lat, engine.station_lon)
    coverage_grid = build_rf_probability_field(distance_df)
    return {
        "azimuth_df": azimuth_df,
        "coverage_grid": coverage_grid,
    }


__all__ = [
    "build_analysis_dataset_impl",
    "build_observations_impl",
    "compute_metrics_impl",
    "run_rf_models_impl",
]



