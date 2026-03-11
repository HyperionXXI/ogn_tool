from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class RFAnalysisDataset:
    """Typed container for stable RFAnalysisEngine dataset outputs.

    Reference:
        docs/core/RF_DATASET_SCHEMA.md

    This class documents the intended engine dataset contract while preserving
    current runtime behavior (the engine still returns a dictionary).

    Stable attributes:
        rf_receptions:
            Description: Canonical reception-like observations used by UI and
                downstream analysis.
            Type: pandas.DataFrame
            Stability: stable

        station_metrics:
            Description: Per-station aggregated metrics (packets, ranges,
                contribution indicators).
            Type: pandas.DataFrame
            Stability: stable

        coverage_grid:
            Description: Spatial coverage grid for map and propagation views.
            Type: pandas.DataFrame
            Stability: stable

        network_metrics:
            Description: Network-level KPI dictionary (station count,
                redundancy, resilience).
            Type: dict[str, Any]
            Stability: stable

        station_overlap_matrix:
            Description: Station-to-station overlap matrix (shared events).
            Type: pandas.DataFrame
            Stability: stable

        rf_diagnosis:
            Description: RF health and issues summary.
            Type: dict[str, Any]
            Stability: stable

    Experimental attributes:
        coverage_redundancy_grid:
            Description: Cell-level redundancy estimates.
            Type: pandas.DataFrame | None
            Stability: experimental

        azimuth_histogram:
            Description: Directional reception histogram.
            Type: Any | None
            Stability: experimental

        directional_balance:
            Description: Directional balance score derived from azimuth data.
            Type: float | None
            Stability: experimental

        shadow_map:
            Description: RF shadow-zone proxy output.
            Type: Any | None
            Stability: experimental

        blind_cells:
            Description: Low-redundancy cells inferred from network reception.
            Type: pandas.DataFrame | None
            Stability: experimental
    """

    rf_receptions: pd.DataFrame
    station_metrics: pd.DataFrame
    coverage_grid: pd.DataFrame
    network_metrics: dict[str, Any]
    station_overlap_matrix: pd.DataFrame
    rf_diagnosis: dict[str, Any]

    coverage_redundancy_grid: pd.DataFrame | None = None
    azimuth_histogram: Any | None = None
    directional_balance: float | None = None
    shadow_map: Any | None = None
    blind_cells: pd.DataFrame | None = None

    @classmethod
    def from_dataset_dict(cls, dataset: dict[str, Any]) -> "RFAnalysisDataset":
        """Build RFAnalysisDataset from the current engine dataset dictionary.

        Reference:
            docs/core/RF_DATASET_SCHEMA.md
        """
        return cls(
            rf_receptions=_as_df(dataset.get("rf_receptions")),
            station_metrics=_as_df(dataset.get("station_metrics")),
            coverage_grid=_as_df(dataset.get("coverage_grid")),
            network_metrics=_as_dict(dataset.get("network_metrics")),
            station_overlap_matrix=_as_df(dataset.get("station_overlap_matrix")),
            rf_diagnosis=_as_dict(dataset.get("rf_diagnosis")),
            coverage_redundancy_grid=_as_optional_df(dataset.get("coverage_redundancy_grid")),
            azimuth_histogram=dataset.get("azimuth_histogram"),
            directional_balance=_as_optional_float(dataset.get("directional_balance")),
            shadow_map=dataset.get("shadow_map"),
            blind_cells=_as_optional_df(dataset.get("blind_cells")),
        )


def _as_df(value: Any) -> pd.DataFrame:
    if isinstance(value, pd.DataFrame):
        return value
    return pd.DataFrame()


def _as_optional_df(value: Any) -> pd.DataFrame | None:
    if value is None:
        return None
    if isinstance(value, pd.DataFrame):
        return value
    return pd.DataFrame()


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _as_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None