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
from ogn_tool.analysis.azimuth import compute_azimuth_histogram, analyze_directional_balance
from ogn_tool.analysis.geo import compute_distance_bearing
from ogn_tool.analysis.network_analysis import detect_network_blind_zones
from ogn_tool.analysis.rf_diagnosis import RFDiagnosis
from ogn_tool.analysis.shadow import detect_rf_shadows
from ogn_tool.analysis.rf_observations import build_rf_observations, compute_distance, compute_bearing
from ogn_tool.analysis.observation_pipeline import build_observations_from_packets
from ogn_tool.engine.observation_builder import ObservationBuilder
from ogn_tool.engine.station_registry import StationRegistry
from ogn_tool.rf_probability_field import build_rf_probability_field
from ogn_tool.models.rf.rf_model_adapter import run_rf_model

from .results import RFAnalysisResult


class RFAnalysisEngine:
    def __init__(self, packets_df: pd.DataFrame, station_lat: float, station_lon: float):
        self.packets = packets_df if packets_df is not None else pd.DataFrame()
        self.station_lat = station_lat
        self.station_lon = station_lon
        self.station_registry = StationRegistry()
        self.observation_builder = ObservationBuilder(self.station_registry)
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


    def build_analysis_dataset(self, dataset_mode: str = "NETWORK", station_id: str | None = None) -> dict:
        packets_all = self.packets.copy()
        if "receiver" in packets_all.columns and "igate" not in packets_all.columns:
            packets_all["igate"] = packets_all["receiver"]
        packets_all = packets_all.reset_index(drop=False).rename(columns={"index": "_row_id"})
        packet_rows = packets_all.to_dict("records")
        observations = build_observations_from_packets(
            packet_rows,
            self.observation_builder,
        )
        rows = observations_to_rows(observations)
        observations_df = pd.DataFrame(rows)
        if "_row_id" not in observations_df.columns:
            observations_df["_row_id"] = pd.Series(dtype="int")
        packets_all = packets_all.merge(
            observations_df,
            on="_row_id",
            how="left",
            suffixes=("", "_obs"),
        )

        # Ensure we keep canonical lat/lon/ts_epoch columns for downstream analysis
        for col in ["lat", "lon", "ts_epoch"]:
            x = f"{col}_x"
            y = f"{col}_y"
            obs = f"{col}_obs"
            if col not in packets_all.columns:
                if obs in packets_all.columns:
                    packets_all[col] = packets_all[obs]
                elif x in packets_all.columns and y in packets_all.columns:
                    packets_all[col] = packets_all[y].fillna(packets_all[x])
            # Clean up any intermediate merged columns
            for drop_col in [x, y, obs]:
                if drop_col in packets_all.columns:
                    packets_all.drop(columns=[drop_col], inplace=True)
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
            # STRICT_RF
            if "qas" in packets_all.columns:
                qas_upper = packets_all["qas"].astype(str).str.upper()
                packets_rf = packets_all[qas_upper.isin(["QAR", "QAO"])].copy()
            packets_filtered = packets_rf

        # Compute geometric metrics for RF packets (distance/bearing from station)
        if "receiver" in packets_rf.columns:
            packets_rf["distance_km"] = compute_distance(packets_rf, self.station_lat, self.station_lon)
            packets_rf["bearing_deg"] = compute_bearing(packets_rf, self.station_lat, self.station_lon)
        elif "lat" in packets_rf.columns and "lon" in packets_rf.columns:
            lat = packets_rf["lat"].to_numpy()
            lon = packets_rf["lon"].to_numpy()

            distance_km, bearing_deg = compute_distance_bearing(
                lat,
                lon,
                station_lat=self.station_lat,
                station_lon=self.station_lon,
            )

            packets_rf["distance_km"] = distance_km
            packets_rf["bearing_deg"] = bearing_deg

        if "distance_km" in packets_filtered.columns:
            packets_filtered["station_range_km"] = packets_filtered["distance_km"]

        if "altitude" in packets_filtered.columns and "altitude_m" not in packets_filtered.columns:
            packets_filtered["altitude_m"] = pd.to_numeric(packets_filtered["altitude"], errors="coerce")

        azimuth_histogram = None
        directional_balance = None
        rf_diagnosis = None
        if "bearing_deg" in packets_rf.columns and len(packets_rf) > 0:
            azimuth_histogram = compute_azimuth_histogram(packets_rf["bearing_deg"])
            if azimuth_histogram is not None:
                directional_balance = analyze_directional_balance(azimuth_histogram)

        # rf_diagnosis will be computed after station/network metrics are built
        rf_issues = []
        rf_health = "UNKNOWN"

        stations = []
        if not packets_filtered.empty and "igate" in packets_filtered.columns:
            stations = sorted(packets_filtered["igate"].astype(str).dropna().unique().tolist())

        distance_df, _grid = build_rf_dataset(packets_filtered, self.station_lat, self.station_lon)
        coverage_grid = build_rf_probability_field(distance_df)
        shadow_map = None

        if azimuth_histogram is not None and directional_balance is not None:
            shadow_map = detect_rf_shadows(
                packets_filtered,
                azimuth_histogram,
                directional_balance,
                station_lat=self.station_lat,
                station_lon=self.station_lon,
            )

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
            station_metrics_df = (
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
            for callsign in station_metrics_df["igate"].tolist():
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
            station_metrics = station_metrics_df.merge(contrib_df, on="igate", how="left")

        coverage_cells = int((coverage_grid["packets"] > 0).sum()) if not coverage_grid.empty and "packets" in coverage_grid.columns else 0

        radio_events = self.build_radio_events(packets_filtered)
        station_reception = self.build_station_reception(packets_filtered)
        coverage_redundancy_grid = self.compute_coverage_redundancy(radio_events, station_reception)
        blind_cells = self.compute_blind_zones(coverage_redundancy_grid)
        station_overlap_matrix = self.compute_station_overlap(station_reception)

        network_blind_zones = detect_network_blind_zones(coverage_redundancy_grid)

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

        # Build extended metrics for RF diagnosis, even when RSSI/noise data is missing
        metrics: dict[str, Any] = {
            "p95_range_km": station_metrics["p95_distance"].max() if not station_metrics.empty else None,
            "max_range_km": station_metrics["max_distance"].max() if not station_metrics.empty else None,
            "coverage_cells": network_metrics.get("coverage_cells"),
            "redundancy_cells": network_metrics.get("redundancy_cells"),
            "network_resilience_score": network_metrics.get("network_resilience_score"),
        }

        if "snr" in packets_filtered.columns:
            metrics["snr"] = float(packets_filtered["snr"].dropna().mean())
        elif "snr_db" in packets_filtered.columns:
            metrics["snr"] = float(packets_filtered["snr_db"].dropna().mean())
        elif "rssi_db" in packets_filtered.columns:
            metrics["rssi"] = float(packets_filtered["rssi_db"].dropna().mean())
        elif "rssi" in packets_filtered.columns:
            metrics["rssi"] = float(packets_filtered["rssi"].dropna().mean())

        if "noise_floor" in packets_filtered.columns:
            metrics["noise_floor"] = float(packets_filtered["noise_floor"].dropna().mean())

        if "packet_loss" in packets_filtered.columns:
            metrics["packet_loss"] = float(packets_filtered["packet_loss"].dropna().mean())

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
        self._last_dataset = dataset
        self._last_dataset_mode = dataset_mode
        self._last_station_id = station_id
        return dataset


    def _get_dataset(self, dataset_mode: str | None = None, station_id: str | None = None) -> dict:
        if self._last_dataset is not None:
            return self._last_dataset
        return self.build_analysis_dataset(
            dataset_mode=dataset_mode or self._last_dataset_mode or "NETWORK",
            station_id=station_id or self._last_station_id,
        )

    def run_station_analysis(self, dataset_mode: str | None = None, station_id: str | None = None) -> Dict[str, Any]:
        dataset = self._get_dataset(dataset_mode=dataset_mode, station_id=station_id)
        return {
            "station_metrics": dataset.get("station_metrics"),
            "coverage_grid": dataset.get("coverage_grid"),
            "azimuth_histogram": dataset.get("azimuth_histogram"),
            "directional_balance": dataset.get("directional_balance"),
        }

    def run_network_analysis(self, dataset_mode: str | None = None, station_id: str | None = None) -> Dict[str, Any]:
        dataset = self._get_dataset(dataset_mode=dataset_mode, station_id=station_id)
        return {
            "network_metrics": dataset.get("network_metrics"),
            "coverage_redundancy_grid": dataset.get("coverage_redundancy_grid"),
            "station_overlap_matrix": dataset.get("station_overlap_matrix"),
            "network_blind_zones": dataset.get("network_blind_zones"),
        }

    def run_rf_diagnostics(self, dataset_mode: str | None = None, station_id: str | None = None) -> Dict[str, Any]:
        dataset = self._get_dataset(dataset_mode=dataset_mode, station_id=station_id)
        return {
            "rf_diagnosis": dataset.get("rf_diagnosis"),
            "shadow_map": dataset.get("shadow_map"),
        }

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

    def _build_observations(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        distance_df, grid = build_rf_dataset(self.packets, self.station_lat, self.station_lon)

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

    def _compute_metrics(
        self,
        distance_df: pd.DataFrame,
        grid_for_analysis: pd.DataFrame,
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        range_stats = analysis_station_range.analyze(grid_for_analysis)
        quality_stats = analysis_station_quality.analyze(grid_for_analysis)
        signal_stats = run_rf_model(analysis_signal_distance.analyze, df_observations=distance_df, station_lat=self.station_lat, station_lon=self.station_lon)
        altitude_stats = run_rf_model(analysis_altitude_distance.analyze, df_observations=distance_df, station_lat=self.station_lat, station_lon=self.station_lon)
        horizon_stats = run_rf_model(analysis_radio_horizon.analyze, df_observations=distance_df, station_lat=self.station_lat, station_lon=self.station_lon)
        terrain_stats = run_rf_model(analysis_terrain.analyze, df_grid=grid_for_analysis, station_lat=self.station_lat, station_lon=self.station_lon)
        visibility_stats = run_rf_model(analysis_terrain_visibility.analyze, df_observations=distance_df, station_lat=self.station_lat, station_lon=self.station_lon)

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

    def _run_rf_models(
        self,
        distance_df: pd.DataFrame,
    ) -> Dict[str, Any]:
        azimuth_df = analysis_azimuth.compute_azimuth_radiation(distance_df, self.station_lat, self.station_lon)
        coverage_grid = build_rf_probability_field(distance_df)
        return {
            "azimuth_df": azimuth_df,
            "coverage_grid": coverage_grid,
        }

    def _run_diagnostics(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        _ = metrics
        return {}

    def _run_network_analysis(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        _ = metrics
        return {}

    def run(self) -> RFAnalysisResult:
        # Stage 1: observation building
        distance_df, grid_for_analysis = self._build_observations()

        # Stage 2: metric computation
        metrics, terrain_stats = self._compute_metrics(distance_df, grid_for_analysis)

        # Stage 3: RF propagation analysis
        rf_models = self._run_rf_models(distance_df)
        azimuth_df = rf_models.get("azimuth_df")
        coverage_grid = rf_models.get("coverage_grid")

        # Stage 4: diagnostics
        _ = self._run_diagnostics(metrics)

        # Stage 5: network intelligence (no-op for run)
        _ = self._run_network_analysis(metrics)

        terrain_mask = terrain_stats.get("data") if terrain_stats.get("implemented") else None

        return RFAnalysisResult(
            packets=self.packets,
            distance_df=distance_df,
            azimuth_df=azimuth_df,
            coverage_grid=coverage_grid,
            terrain_mask=terrain_mask,
            metrics=metrics,
        )



from typing import Iterable, List

from ogn_tool.domain.rf_observation import RFObservation


def observations_to_rows(observations: Iterable[RFObservation]) -> List[dict]:
    """
    Temporary compatibility layer.

    Converts RFObservation objects back into the row-like dictionaries
    expected by existing analysis modules.

    This allows progressive migration of analysis code to RFObservation
    without breaking the current system.
    """

    rows = []

    for obs in observations:
        event = obs.event

        rows.append(
            {
                "lat": event.lat,
                "lon": event.lon,
                "ts_epoch": event.timestamp,
                "aircraft": event.emitter_id,
                "igate": event.receiver_id,
                "_row_id": event.metadata.get("_row_id") if event.metadata else None,
                "receiver_lat": obs.receiver_lat,
                "receiver_lon": obs.receiver_lon,
                "receiver_alt": obs.receiver_alt,
                "distance_km": obs.distance_km,
                "bearing_deg": obs.bearing_deg,
            }
        )

    return rows





