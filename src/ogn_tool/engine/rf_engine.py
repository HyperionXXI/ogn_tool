from __future__ import annotations

from typing import Any, Dict, List, Optional

import importlib
import pandas as pd

from ogn_tool.models.rf_analysis_dataset import RFAnalysisDataset
from ogn_tool.models.rf_analysis_results import RFAnalysisResults
from ogn_tool.models.rf_observation_vector import RFObservationVector

from .rf_dataset_builder import build_dataset, build_observation_payload
from .rf_pipeline_executor import execute_rf_pipeline
from .rf_metrics_aggregator import aggregate_metrics
from .rf_engine_network import (
    build_radio_events as _build_radio_events,
    build_station_reception as _build_station_reception,
    compute_coverage_redundancy as _compute_coverage_redundancy,
    compute_blind_zones as _compute_blind_zones,
    compute_station_overlap as _compute_station_overlap,
    inspect_zone_impl,
)


class RFAnalysisEngine:
    def __init__(self, packets_df: pd.DataFrame | None = None, station_lat: float = 0.0, station_lon: float = 0.0):
        self.packets = packets_df if packets_df is not None else pd.DataFrame()
        self.station_lat = station_lat
        self.station_lon = station_lon
        self._last_dataset: Optional[dict] = None
        self._last_dataset_mode: Optional[str] = None
        self._last_station_id: Optional[str] = None

        pipeline_mod = importlib.import_module("ogn_tool.pipeline.rf_analysis_pipeline")
        stages_mod = importlib.import_module("ogn_tool.pipeline.rf_stages")
        self.pipeline = pipeline_mod.RFAnalysisPipeline([
            stages_mod.FeatureMatrixStage(),
            stages_mod.RFCoverageStage(),
            stages_mod.VisibilityModelStage(),
            stages_mod.BlindZoneDetectionStage(),
            stages_mod.AntennaPatternStage(),
            stages_mod.RFDiagnosticsStage(),
        ])

    @staticmethod
    def filter_packets_by_station(packets_rf: pd.DataFrame, station_id: str) -> pd.DataFrame:
        if packets_rf is None or packets_rf.empty or not station_id:
            return packets_rf if packets_rf is not None else pd.DataFrame()
        if "igate" not in packets_rf.columns:
            return packets_rf.iloc[0:0].copy()
        return packets_rf[packets_rf["igate"].astype(str) == station_id]

    def build_analysis_dataset(self, dataset_mode: str = "NETWORK", station_id: str | None = None) -> dict:
        return build_dataset(self, dataset_mode=dataset_mode, station_id=station_id)

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
        return inspect_zone_impl(self, lat=lat, lon=lon, radius_km=radius_km)

    @staticmethod
    def build_radio_events(packets_df: pd.DataFrame) -> pd.DataFrame:
        return _build_radio_events(packets_df)

    @staticmethod
    def build_station_reception(packets_df: pd.DataFrame) -> pd.DataFrame:
        return _build_station_reception(packets_df)

    @staticmethod
    def compute_coverage_redundancy(radio_events: pd.DataFrame, station_reception: pd.DataFrame) -> pd.DataFrame:
        return _compute_coverage_redundancy(radio_events, station_reception)

    @staticmethod
    def compute_blind_zones(coverage_redundancy: pd.DataFrame) -> pd.DataFrame:
        return _compute_blind_zones(coverage_redundancy)

    @staticmethod
    def compute_station_overlap(station_reception: pd.DataFrame) -> pd.DataFrame:
        return _compute_station_overlap(station_reception)

    def _build_observation_inputs(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        from .rf_engine_dataset_builder import build_observations_impl

        return build_observations_impl(self)


    def run(self, dataset: RFAnalysisDataset) -> RFAnalysisResults:
        distance_df, grid_for_analysis = self._build_observation_inputs()

        existing_vectors = []
        if isinstance(dataset.observations, list):
            existing_vectors = dataset.observations
        elif isinstance(dataset.observations, dict):
            existing_vectors = dataset.observations.get("vectors", []) or []

        dataset.observations = build_observation_payload(
            distance_df=distance_df,
            station_lat=self.station_lat,
            station_lon=self.station_lon,
            vectors=existing_vectors,
            grid_for_analysis=grid_for_analysis,
            timestamp=distance_df.get("ts_epoch") if hasattr(distance_df, "get") else None,
            timestamp_ns=distance_df.get("ts_ns") if hasattr(distance_df, "get") else None,
        )

        dataset = execute_rf_pipeline(dataset, self.pipeline)
        dataset.validate()

        metrics = dataset.results.metrics or {}
        metrics["distance_df"] = distance_df
        dataset.results.metrics = metrics
        aggregate_metrics(dataset)

        previous_graph = getattr(dataset.results, "network_graph", None)
        network_stage = importlib.import_module("ogn_tool.pipeline.network_graph_stage")
        network = network_stage.run_network_graph_stage(dataset, previous_graph=previous_graph)
        dataset.network_graph = network["graph"]
        dataset.results.network_graph = network["graph"]
        dataset.results.network_metrics = network["metrics"]
        dataset.results.network_timeseries = network["timeseries"]
        dataset.results.network_events = network["events"]
        dataset.results.network_evolution = network["evolution"]
        dataset.results.station_suggestions = network["station_suggestions"]

        # Attach spatial_observations to results if present in network stage output
        if "spatial_observations" in network:
            dataset.results.spatial_observations = network["spatial_observations"]
        else:
            # Try to build from observations as fallback
            try:
                from ogn_tool.analysis.observation_views import build_spatial_observation_frame
                dataset.results.spatial_observations = build_spatial_observation_frame(dataset.observations)
            except Exception:
                dataset.results.spatial_observations = None

        return dataset.results

    def run_from_observations(self, observations: Optional[List[RFObservationVector]] = None) -> RFAnalysisResults:
        dataset = RFAnalysisDataset(observations=observations or [])
        return self.run(dataset)
