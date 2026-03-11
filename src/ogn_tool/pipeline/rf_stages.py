from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from ogn_tool.analysis import azimuth as analysis_azimuth
from ogn_tool.analysis import station_quality as analysis_station_quality
from ogn_tool.analysis import station_range as analysis_station_range
from ogn_tool.analysis import signal_distance as analysis_signal_distance
from ogn_tool.analysis import altitude_distance as analysis_altitude_distance
from ogn_tool.analysis import radio_horizon as analysis_radio_horizon
from ogn_tool.analysis import terrain as analysis_terrain
from ogn_tool.analysis import terrain_visibility as analysis_terrain_visibility
from ogn_tool.analysis.network_analysis import detect_network_blind_zones
from ogn_tool.models.rf.rf_model_adapter import run_rf_model
from ogn_tool.rf_probability_field import build_rf_probability_field

from .rf_stage import RFAnalysisStage


class RFCoverageStage(RFAnalysisStage):
    def run(self, dataset: Dict[str, Any]) -> Dict[str, Any]:
        distance_df: pd.DataFrame = dataset.get("distance_df")
        if distance_df is None:
            distance_df = pd.DataFrame()
        station_lat = dataset.get("station_lat")
        station_lon = dataset.get("station_lon")

        azimuth_df = analysis_azimuth.compute_azimuth_radiation(distance_df, station_lat, station_lon)
        coverage_grid = build_rf_probability_field(distance_df)

        dataset["azimuth_df"] = azimuth_df
        dataset["coverage_grid"] = coverage_grid
        return dataset


class VisibilityModelStage(RFAnalysisStage):
    def run(self, dataset: Dict[str, Any]) -> Dict[str, Any]:
        distance_df: pd.DataFrame = dataset.get("distance_df")
        grid_for_analysis: pd.DataFrame = dataset.get("grid_for_analysis")
        station_lat = dataset.get("station_lat")
        station_lon = dataset.get("station_lon")

        if distance_df is None:
            distance_df = pd.DataFrame()
        if grid_for_analysis is None:
            grid_for_analysis = pd.DataFrame()

        range_stats = analysis_station_range.analyze(grid_for_analysis)
        quality_stats = analysis_station_quality.analyze(grid_for_analysis)
        signal_stats = run_rf_model(
            analysis_signal_distance.analyze,
            df_observations=distance_df,
            station_lat=station_lat,
            station_lon=station_lon,
        )
        altitude_stats = run_rf_model(
            analysis_altitude_distance.analyze,
            df_observations=distance_df,
            station_lat=station_lat,
            station_lon=station_lon,
        )
        horizon_stats = run_rf_model(
            analysis_radio_horizon.analyze,
            df_observations=distance_df,
            station_lat=station_lat,
            station_lon=station_lon,
        )
        terrain_stats = run_rf_model(
            analysis_terrain.analyze,
            df_grid=grid_for_analysis,
            station_lat=station_lat,
            station_lon=station_lon,
        )
        visibility_stats = run_rf_model(
            analysis_terrain_visibility.analyze,
            df_observations=distance_df,
            station_lat=station_lat,
            station_lon=station_lon,
        )

        metrics = dataset.setdefault("metrics", {})
        metrics.update(
            {
                "station_range": range_stats,
                "station_quality": quality_stats,
                "signal_distance": signal_stats,
                "altitude_distance": altitude_stats,
                "radio_horizon": horizon_stats,
                "terrain": terrain_stats,
                "terrain_visibility": visibility_stats,
            }
        )

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

        dataset["terrain"] = terrain_stats
        dataset["metrics"] = metrics
        return dataset


class BlindZoneDetectionStage(RFAnalysisStage):
    def run(self, dataset: Dict[str, Any]) -> Dict[str, Any]:
        coverage_grid: pd.DataFrame = dataset.get("coverage_grid")
        distance_df: pd.DataFrame = dataset.get("distance_df")

        source = coverage_grid if isinstance(coverage_grid, pd.DataFrame) and not coverage_grid.empty else distance_df
        blind_zone_grid = detect_network_blind_zones(source)
        dataset["blind_zone_grid"] = blind_zone_grid
        return dataset


class RFDiagnosticsStage(RFAnalysisStage):
    def run(self, dataset: Dict[str, Any]) -> Dict[str, Any]:
        metrics = dataset.setdefault("metrics", {})
        metrics["rf_models"] = {
            "signal_distance": metrics.get("signal_distance"),
            "radio_horizon": metrics.get("radio_horizon"),
            "terrain": metrics.get("terrain"),
            "terrain_visibility": metrics.get("terrain_visibility"),
            "altitude_distance": metrics.get("altitude_distance"),
        }
        if "blind_zone_grid" in dataset:
            metrics["blind_zone_grid"] = dataset.get("blind_zone_grid")
        dataset["metrics"] = metrics
        return dataset


__all__ = [
    "RFCoverageStage",
    "VisibilityModelStage",
    "BlindZoneDetectionStage",
    "RFDiagnosticsStage",
]
