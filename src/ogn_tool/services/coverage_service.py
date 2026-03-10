"""Coverage-related service wrappers."""

from __future__ import annotations

from typing import Optional

import pandas as pd

from ogn_tool.engine.rf_engine import RFAnalysisEngine


def build_coverage_grid(
    packets_df: pd.DataFrame,
    station_lat: float,
    station_lon: float,
    dataset_mode: str = "STRICT_RF",
    station_id: Optional[str] = None,
):
    """
    Build and return the coverage grid from the RF engine dataset.

    This isolates UI/API code from direct engine orchestration.
    """
    engine = RFAnalysisEngine(packets_df, station_lat, station_lon)
    dataset = engine.build_analysis_dataset(dataset_mode=dataset_mode, station_id=station_id)
    return dataset.get("coverage_grid")
