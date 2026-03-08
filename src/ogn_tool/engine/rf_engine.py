from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from ogn_tool.analysis.pipeline import build_rf_dataset
from ogn_tool.analysis import azimuth as analysis_azimuth
from ogn_tool.analysis import station_range as analysis_station_range
from ogn_tool.analysis import station_quality as analysis_station_quality
from ogn_tool.analysis import signal_distance as analysis_signal_distance
from ogn_tool.analysis import altitude_distance as analysis_altitude_distance
from ogn_tool.analysis import radio_horizon as analysis_radio_horizon
from ogn_tool.analysis import terrain as analysis_terrain
from ogn_tool.analysis import terrain_visibility as analysis_terrain_visibility
from ogn_tool.rf_probability_field import build_rf_probability_field

from .results import RFAnalysisResult


class RFAnalysisEngine:
    def __init__(self, packets_df: pd.DataFrame, station_lat: float, station_lon: float):
        self.packets = packets_df if packets_df is not None else pd.DataFrame()
        self.station_lat = station_lat
        self.station_lon = station_lon


    def build_analysis_dataset(self) -> dict:
        packets_all = self.packets.copy()
        packets_filtered = packets_all
        packets_rf = packets_all.iloc[0:0].copy()
        if "qas" in packets_all.columns:
            qas_upper = packets_all["qas"].astype(str).str.upper()
            packets_rf = packets_all[qas_upper.isin(["QAR", "QAO"])].copy()
        distance_df, _grid = build_rf_dataset(packets_filtered, self.station_lat, self.station_lon)
        coverage_grid = build_rf_probability_field(distance_df)
        return {
            "packets_all": packets_all,
            "packets_rf": packets_rf,
            "packets_filtered": packets_filtered,
            "coverage_grid": coverage_grid,
        }

    def run(self) -> RFAnalysisResult:
        distance_df, grid = build_rf_dataset(self.packets, self.station_lat, self.station_lon)
        azimuth_df = analysis_azimuth.compute_azimuth_radiation(distance_df, self.station_lat, self.station_lon)

        coverage_grid = build_rf_probability_field(distance_df)

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

        range_stats = analysis_station_range.analyze(grid_for_analysis)
        quality_stats = analysis_station_quality.analyze(grid_for_analysis)
        signal_stats = analysis_signal_distance.analyze(distance_df, station_lat=self.station_lat, station_lon=self.station_lon)
        altitude_stats = analysis_altitude_distance.analyze(distance_df, station_lat=self.station_lat, station_lon=self.station_lon)
        horizon_stats = analysis_radio_horizon.analyze(distance_df, station_lat=self.station_lat, station_lon=self.station_lon)
        terrain_stats = analysis_terrain.analyze(grid_for_analysis, station_lat=self.station_lat, station_lon=self.station_lon)
        visibility_stats = analysis_terrain_visibility.analyze(distance_df, station_lat=self.station_lat, station_lon=self.station_lon)

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

        terrain_mask = terrain_stats.get("data") if terrain_stats.get("implemented") else None

        return RFAnalysisResult(
            packets=self.packets,
            distance_df=distance_df,
            azimuth_df=azimuth_df,
            coverage_grid=coverage_grid,
            terrain_mask=terrain_mask,
            metrics=metrics,
        )
