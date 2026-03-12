from __future__ import annotations

import pandas as pd

from ogn_tool.analysis import altitude_distance as analysis_altitude_distance
from ogn_tool.analysis import radio_horizon as analysis_radio_horizon
from ogn_tool.analysis import terrain as analysis_terrain
from ogn_tool.analysis import terrain_visibility as analysis_terrain_visibility
from ogn_tool.analysis.network_analysis import detect_network_blind_zones
from ogn_tool.models.rf.rf_model_adapter import run_rf_model
from ogn_tool.models.rf_analysis_dataset import RFAnalysisDataset
from ogn_tool.network import station_quality as analysis_station_quality
from ogn_tool.network import station_range as analysis_station_range
from ogn_tool.rf import azimuth as analysis_azimuth
from ogn_tool.rf import signal_distance as analysis_signal_distance
from ogn_tool.rf_probability_field import build_rf_probability_field

from .rf_stage import RFAnalysisStage


class FeatureMatrixStage(RFAnalysisStage):
    name = "feature_matrix"
    requires = ["observations"]
    produces = ["feature_matrix"]

    def run(self, dataset: RFAnalysisDataset) -> RFAnalysisDataset:
        from ogn_tool.analysis.rf_feature_matrix import build_feature_matrix

        dataset.feature_matrix = build_feature_matrix(dataset.observations)
        return dataset


class RFCoverageStage(RFAnalysisStage):
    name = "coverage"
    requires = ["feature_matrix"]
    produces = ["coverage"]

    def run(self, dataset: RFAnalysisDataset) -> RFAnalysisDataset:
        distance_df = getattr(dataset, "distance_df", None)
        if distance_df is None:
            distance_df = pd.DataFrame()
        station_lat = getattr(dataset, "station_lat", None)
        station_lon = getattr(dataset, "station_lon", None)

        if callable(getattr(analysis_azimuth, "compute_azimuth_radiation", None)):
            azimuth_df = analysis_azimuth.compute_azimuth_radiation(distance_df, station_lat, station_lon)
        else:
            azimuth_df = pd.DataFrame()
        if {"lat", "lon"}.issubset(distance_df.columns):
            coverage_grid = build_rf_probability_field(distance_df)
        else:
            coverage_grid = pd.DataFrame()

        dataset.results.coverage = coverage_grid
        metrics = dataset.results.metrics or {}
        metrics["azimuth_df"] = azimuth_df
        dataset.results.metrics = metrics
        return dataset


class VisibilityModelStage(RFAnalysisStage):
    name = "visibility"
    requires = ["coverage"]
    produces = ["visibility"]

    def run(self, dataset: RFAnalysisDataset) -> RFAnalysisDataset:
        distance_df = getattr(dataset, "distance_df", None)
        grid_for_analysis = getattr(dataset, "grid_for_analysis", None)
        station_lat = getattr(dataset, "station_lat", None)
        station_lon = getattr(dataset, "station_lon", None)

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

        metrics = dataset.results.metrics or {}
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

        dataset.results.visibility = {
            "signal_distance": signal_stats,
            "radio_horizon": horizon_stats,
            "terrain_visibility": visibility_stats,
        }
        dataset.results.metrics = metrics
        return dataset


class BlindZoneDetectionStage(RFAnalysisStage):
    name = "blind_zone"
    requires = ["visibility"]
    produces = ["blind_zones"]

    def run(self, dataset: RFAnalysisDataset) -> RFAnalysisDataset:
        coverage_grid = dataset.results.coverage
        distance_df = getattr(dataset, "distance_df", None)

        source = coverage_grid if isinstance(coverage_grid, pd.DataFrame) and not coverage_grid.empty else distance_df
        blind_zone_grid = detect_network_blind_zones(source)
        dataset.results.blind_zones = blind_zone_grid
        return dataset


class AntennaPatternStage(RFAnalysisStage):

    name = "antenna_pattern"
    requires = ["feature_matrix"]
    produces = ["antenna_pattern", "antenna_shadow_sectors"]

    def run(self, dataset: RFAnalysisDataset) -> RFAnalysisDataset:

        from ogn_tool.analysis.rf_antenna_pattern import estimate_antenna_pattern, detect_shadow_sectors

        pattern = estimate_antenna_pattern(dataset.feature_matrix)

        dataset.results.antenna_pattern = pattern
        dataset.results.antenna_shadow_sectors = detect_shadow_sectors(pattern)

        return dataset


class RFDiagnosticsStage(RFAnalysisStage):
    name = "diagnostics"
    requires = ["coverage", "visibility"]
    produces = ["metrics"]

    def run(self, dataset: RFAnalysisDataset) -> RFAnalysisDataset:
        metrics = dataset.results.metrics or {}
        metrics["rf_models"] = {
            "signal_distance": metrics.get("signal_distance"),
            "radio_horizon": metrics.get("radio_horizon"),
            "terrain": metrics.get("terrain"),
            "terrain_visibility": metrics.get("terrain_visibility"),
            "altitude_distance": metrics.get("altitude_distance"),
        }
        if dataset.results.blind_zones is not None:
            metrics["blind_zone_grid"] = dataset.results.blind_zones
        if dataset.results.antenna_pattern is not None:
            metrics["antenna_pattern"] = dataset.results.antenna_pattern
        if dataset.results.antenna_shadow_sectors is not None:
            metrics["antenna_shadow_sectors"] = dataset.results.antenna_shadow_sectors

        dataset.results.metrics = metrics
        return dataset


__all__ = [
    "FeatureMatrixStage",
    "RFCoverageStage",
    "VisibilityModelStage",
    "BlindZoneDetectionStage",
    "AntennaPatternStage",
    "RFDiagnosticsStage",
]


