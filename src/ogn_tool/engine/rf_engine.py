from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
import numpy as np

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
        self._last_dataset: Optional[dict] = None
        self._last_dataset_mode: Optional[str] = None
        self._last_station_id: Optional[str] = None

    @staticmethod
    def filter_packets_by_station(packets_rf: pd.DataFrame, station_id: str) -> pd.DataFrame:
        if packets_rf is None or packets_rf.empty or not station_id:
            return packets_rf if packets_rf is not None else pd.DataFrame()
        if "igate" not in packets_rf.columns:
            return packets_rf.iloc[0:0].copy()
        return packets_rf[packets_rf["igate"].astype(str) == station_id]


    def build_analysis_dataset(self, dataset_mode: str = "STRICT_RF", station_id: str | None = None) -> dict:
        packets_all = self.packets.copy()
        packets_filtered = packets_all
        packets_rf = packets_all.iloc[0:0].copy()
        dataset_mode = (dataset_mode or "STRICT_RF").upper()
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
            # STRICT_RF
            if "qas" in packets_all.columns:
                qas_upper = packets_all["qas"].astype(str).str.upper()
                packets_rf = packets_all[qas_upper.isin(["QAR", "QAO"])].copy()
            packets_filtered = packets_rf

        stations = []
        if not packets_filtered.empty and "igate" in packets_filtered.columns:
            stations = sorted(packets_filtered["igate"].astype(str).dropna().unique().tolist())

        distance_df, _grid = build_rf_dataset(packets_filtered, self.station_lat, self.station_lon)
        coverage_grid = build_rf_probability_field(distance_df)

        # enrich coverage_grid with per-cell altitude statistics
        if not distance_df.empty and "lat" in distance_df.columns and "lon" in distance_df.columns:
            cell_size = float(coverage_grid["cell_size_deg"].iloc[0]) if not coverage_grid.empty and "cell_size_deg" in coverage_grid.columns else 0.01
            df_cells = distance_df.copy()
            df_cells["grid_lat"] = (pd.to_numeric(df_cells.get("lat"), errors="coerce") // cell_size) * cell_size
            df_cells["grid_lon"] = (pd.to_numeric(df_cells.get("lon"), errors="coerce") // cell_size) * cell_size
            agg = {
                "max_distance": ("distance_km", "max"),
            }
            if "altitude_m" in df_cells.columns:
                agg["mean_altitude"] = ("altitude_m", "mean")
            cell_stats = (
                df_cells.groupby(["grid_lat", "grid_lon"], dropna=False)
                .agg(**agg)
                .reset_index()
                .rename(columns={"grid_lat": "lat", "grid_lon": "lon"})
            )
            if not coverage_grid.empty:
                coverage_grid = coverage_grid.merge(cell_stats, on=["lat", "lon"], how="left")

        # radio_events: group same transmission heard by multiple stations
        radio_events = pd.DataFrame()
        if not packets_all.empty and "src" in packets_all.columns:
            df_evt = packets_all.copy()
            if "ts_epoch" in df_evt.columns:
                df_evt["time_bucket"] = (pd.to_numeric(df_evt["ts_epoch"], errors="coerce") // 2) * 2
            elif "ts_utc" in df_evt.columns:
                ts = pd.to_datetime(df_evt["ts_utc"], errors="coerce")
                df_evt["time_bucket"] = (ts.view("int64") // 1_000_000_000 // 2) * 2
            else:
                df_evt["time_bucket"] = pd.NA
            if "lat" in df_evt.columns and "lon" in df_evt.columns:
                df_evt["lat_r"] = pd.to_numeric(df_evt["lat"], errors="coerce").round(3)
                df_evt["lon_r"] = pd.to_numeric(df_evt["lon"], errors="coerce").round(3)
            else:
                df_evt["lat_r"] = pd.NA
                df_evt["lon_r"] = pd.NA
            if "igate" not in df_evt.columns:
                df_evt["igate"] = pd.NA
            radio_events = (
                df_evt.groupby(["src", "time_bucket", "lat_r", "lon_r"], dropna=False)
                .agg(
                    packet_count=("src", "size"),
                    station_count=("igate", "nunique"),
                )
                .reset_index()
            )

        # station_metrics
        station_metrics = pd.DataFrame()
        if not distance_df.empty and "igate" in distance_df.columns:
            df_station = distance_df.copy()
            dist = pd.to_numeric(df_station.get("distance_km"), errors="coerce")
            cell_size = float(coverage_grid["cell_size_deg"].iloc[0]) if not coverage_grid.empty and "cell_size_deg" in coverage_grid.columns else 0.01
            df_station["grid_lat"] = (pd.to_numeric(df_station.get("lat"), errors="coerce") // cell_size) * cell_size
            df_station["grid_lon"] = (pd.to_numeric(df_station.get("lon"), errors="coerce") // cell_size) * cell_size
            metrics = (
                df_station.groupby("igate")
                .agg(
                    packet_count=("igate", "size"),
                    aircraft_count=("src", "nunique"),
                    max_distance=("distance_km", "max"),
                    p95_distance=("distance_km", lambda x: pd.Series(x).quantile(0.95)),
                    coverage_cells=("grid_lat", "nunique"),
                )
                .reset_index()
            )
            # unique/shared packet contribution per station
            src_igates = distance_df.groupby("src")["igate"].nunique()
            unique_src = src_igates[src_igates == 1].index
            shared_src = src_igates[src_igates > 1].index
            contrib = []
            for callsign in metrics["igate"].tolist():
                subset = df_station[df_station["igate"] == callsign]
                unique_packets = int(subset[subset["src"].isin(unique_src)].shape[0])
                shared_packets = int(subset[subset["src"].isin(shared_src)].shape[0])
                redundant_packets = shared_packets
                total_packets = int(subset.shape[0])
                contribution_score = (unique_packets / total_packets * 100.0) if total_packets else 0.0
                contrib.append(
                    {
                        "igate": callsign,
                        "unique_packets": unique_packets,
                        "shared_packets": shared_packets,
                        "redundant_packets": redundant_packets,
                        "contribution_score": contribution_score,
                    }
                )
            contrib_df = pd.DataFrame(contrib)
            station_metrics = metrics.merge(contrib_df, on="igate", how="left")

        coverage_cells = int((coverage_grid["packets"] > 0).sum()) if not coverage_grid.empty and "packets" in coverage_grid.columns else 0

        radio_events = self.build_radio_events(packets_filtered)
        station_reception = self.build_station_reception(packets_filtered)
        coverage_redundancy_grid = self.compute_coverage_redundancy(radio_events, station_reception)
        blind_cells = self.compute_blind_zones(coverage_redundancy_grid)
        station_overlap_matrix = self.compute_station_overlap(station_reception)

        # network metrics derived from redundancy grid
        redundancy_cells = int((coverage_redundancy_grid["station_count"] > 1).sum()) if not coverage_redundancy_grid.empty and "station_count" in coverage_redundancy_grid.columns else 0
        blind_cells_count = int(len(blind_cells)) if blind_cells is not None else 0
        network_metrics = {
            "station_count": int(len(station_metrics)) if not station_metrics.empty else 0,
            "coverage_cells": coverage_cells,
            "redundancy_cells": redundancy_cells,
            "blind_cells": blind_cells_count,
            "network_resilience_score": (redundancy_cells / coverage_cells * 100.0) if coverage_cells else 0.0,
        }

        dataset = {
            "packets_all": packets_all,
            "packets_rf": packets_rf,
            "packets_filtered": packets_filtered,
            "radio_events": radio_events,
            "station_reception": station_reception,
            "coverage_grid": coverage_grid,
            "coverage_redundancy_grid": coverage_redundancy_grid,
            "station_metrics": station_metrics,
            "network_metrics": network_metrics,
            "station_overlap_matrix": station_overlap_matrix,
            "blind_cells": blind_cells,
            "stations": stations,
        }
        self._last_dataset = dataset
        self._last_dataset_mode = dataset_mode
        self._last_station_id = station_id
        return dataset

    def inspect_zone(self, lat: float, lon: float, radius_km: float = 5.0) -> dict:
        if lat is None or lon is None:
            return {
                "events_count": 0,
                "stations": [],
                "redundancy_mean": 0.0,
                "max_distance_km": None,
            }

        dataset = self._last_dataset or self.build_analysis_dataset(
            dataset_mode=self._last_dataset_mode or "STRICT_RF",
            station_id=self._last_station_id,
        )
        radio_events = dataset.get("radio_events") or pd.DataFrame()
        station_reception = dataset.get("station_reception") or pd.DataFrame()

        if radio_events.empty or "lat" not in radio_events.columns or "lon" not in radio_events.columns:
            return {
                "events_count": 0,
                "stations": [],
                "redundancy_mean": 0.0,
                "max_distance_km": None,
            }

        lat_r = np.radians(pd.to_numeric(radio_events["lat"], errors="coerce"))
        lon_r = np.radians(pd.to_numeric(radio_events["lon"], errors="coerce"))
        lat0 = np.radians(float(lat))
        lon0 = np.radians(float(lon))
        dlat = lat_r - lat0
        dlon = lon_r - lon0
        a = np.sin(dlat / 2) ** 2 + np.cos(lat0) * np.cos(lat_r) * np.sin(dlon / 2) ** 2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        dist_km = 6371.0 * c
        mask = dist_km <= float(radius_km)
        events_zone = radio_events[mask]

        if events_zone.empty:
            return {
                "events_count": 0,
                "stations": [],
                "redundancy_mean": 0.0,
                "max_distance_km": None,
            }

        stations = []
        max_distance = None
        if not station_reception.empty and "event_key" in station_reception.columns:
            subset = station_reception[station_reception["event_key"].isin(events_zone["event_key"])]
            if "station_id" in subset.columns:
                stations = sorted(subset["station_id"].astype(str).dropna().unique().tolist())
            if "distance_km" in subset.columns:
                max_distance = pd.to_numeric(subset["distance_km"], errors="coerce").max()

        redundancy_mean = (
            pd.to_numeric(events_zone.get("station_count"), errors="coerce").mean()
            if "station_count" in events_zone.columns
            else 0.0
        )

        return {
            "events_count": int(len(events_zone)),
            "stations": stations,
            "redundancy_mean": float(redundancy_mean) if pd.notna(redundancy_mean) else 0.0,
            "max_distance_km": max_distance,
        }

    @staticmethod
    def build_radio_events(packets_df: pd.DataFrame) -> pd.DataFrame:
        if packets_df is None or packets_df.empty or "src" not in packets_df.columns:
            return pd.DataFrame()
        df = packets_df.copy()
        if "ts_epoch" in df.columns:
            df["time_bucket"] = (pd.to_numeric(df["ts_epoch"], errors="coerce") // 2) * 2
        elif "ts_utc" in df.columns:
            ts = pd.to_datetime(df["ts_utc"], errors="coerce")
            df["time_bucket"] = (ts.view("int64") // 1_000_000_000 // 2) * 2
        else:
            df["time_bucket"] = pd.NA
        df["lat_round"] = pd.to_numeric(df.get("lat"), errors="coerce").round(3)
        df["lon_round"] = pd.to_numeric(df.get("lon"), errors="coerce").round(3)
        df["event_key"] = (
            df["src"].astype(str)
            + "_"
            + df["time_bucket"].astype(str)
            + "_"
            + df["lat_round"].astype(str)
            + "_"
            + df["lon_round"].astype(str)
        )
        agg = {
            "timestamp": ("ts_epoch", "min") if "ts_epoch" in df.columns else ("time_bucket", "min"),
            "aircraft": ("src", "first"),
            "lat": ("lat", "mean"),
            "lon": ("lon", "mean"),
            "packet_count": ("src", "size"),
        }
        if "altitude_m" in df.columns:
            agg["altitude"] = ("altitude_m", "mean")
        if "igate" in df.columns:
            agg["station_count"] = ("igate", "nunique")
        events = df.groupby("event_key", dropna=False).agg(**agg).reset_index()
        if "altitude" not in events.columns:
            events["altitude"] = pd.NA
        if "station_count" not in events.columns:
            events["station_count"] = events["packet_count"]
        return events

    @staticmethod
    def build_station_reception(packets_df: pd.DataFrame) -> pd.DataFrame:
        if packets_df is None or packets_df.empty or "src" not in packets_df.columns:
            return pd.DataFrame()
        df = packets_df.copy()
        if "ts_epoch" in df.columns:
            df["time_bucket"] = (pd.to_numeric(df["ts_epoch"], errors="coerce") // 2) * 2
        elif "ts_utc" in df.columns:
            ts = pd.to_datetime(df["ts_utc"], errors="coerce")
            df["time_bucket"] = (ts.view("int64") // 1_000_000_000 // 2) * 2
        else:
            df["time_bucket"] = pd.NA
        df["lat_round"] = pd.to_numeric(df.get("lat"), errors="coerce").round(3)
        df["lon_round"] = pd.to_numeric(df.get("lon"), errors="coerce").round(3)
        df["event_key"] = (
            df["src"].astype(str)
            + "_"
            + df["time_bucket"].astype(str)
            + "_"
            + df["lat_round"].astype(str)
            + "_"
            + df["lon_round"].astype(str)
        )
        cols = ["event_key"]
        if "igate" in df.columns:
            cols.append("igate")
        if "rssi_db" in df.columns:
            cols.append("rssi_db")
        elif "rssi" in df.columns:
            cols.append("rssi")
        if "snr_db" in df.columns:
            cols.append("snr_db")
        elif "snr" in df.columns:
            cols.append("snr")
        if "distance_km" in df.columns:
            cols.append("distance_km")
        return df[cols].rename(columns={"igate": "station_id"})

    @staticmethod
    def compute_coverage_redundancy(radio_events: pd.DataFrame, station_reception: pd.DataFrame) -> pd.DataFrame:
        if radio_events is None or station_reception is None or radio_events.empty or station_reception.empty:
            return pd.DataFrame()
        df = station_reception.merge(
            radio_events[["event_key", "lat", "lon"]],
            on="event_key",
            how="left",
        )
        df["lat_cell"] = (pd.to_numeric(df["lat"], errors="coerce") / 0.05).round() * 0.05
        df["lon_cell"] = (pd.to_numeric(df["lon"], errors="coerce") / 0.05).round() * 0.05
        return (
            df.groupby(["lat_cell", "lon_cell"], dropna=False)
            .agg(
                station_count=("station_id", "nunique"),
                reception_count=("event_key", "count"),
            )
            .reset_index()
        )

    @staticmethod
    def compute_blind_zones(coverage_redundancy: pd.DataFrame) -> pd.DataFrame:
        if coverage_redundancy is None or coverage_redundancy.empty or "station_count" not in coverage_redundancy.columns:
            return pd.DataFrame()
        return coverage_redundancy[coverage_redundancy["station_count"] <= 1].copy()

    @staticmethod
    def compute_station_overlap(station_reception: pd.DataFrame) -> pd.DataFrame:
        if station_reception is None or station_reception.empty:
            return pd.DataFrame()
        if "event_key" not in station_reception.columns or "station_id" not in station_reception.columns:
            return pd.DataFrame()
        incidence = pd.crosstab(station_reception["event_key"], station_reception["station_id"]) > 0
        overlap = incidence.T.dot(incidence)
        return overlap

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
