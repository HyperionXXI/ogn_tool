from __future__ import annotations

from typing import Optional

import pandas as pd

from ogn_tool.models.rf_analysis_results import RFAnalysisResults
from ogn_tool.models.rf_observation_vector import RFObservationVector
from ogn_tool.services.rf_analysis_service import run_rf_analysis


def run_dashboard_analysis(
    packets_df: pd.DataFrame,
    station_lat: float,
    station_lon: float,
    station_id: Optional[str] = None,
    dataset_mode: Optional[str] = None,
    observations: list[RFObservationVector] | None = None,
) -> RFAnalysisResults:
    """Runtime adapter used by dashboard UI.

    The dashboard consumes the typed service entrypoint through this adapter
    instead of calling the engine directly with a synthetic dataset.
    `dataset_mode` is accepted for runtime compatibility even though the typed
    analysis path currently derives its own snapshot internally.
    """
    _ = dataset_mode
    return run_rf_analysis(
        packets_df=packets_df,
        station_lat=station_lat,
        station_lon=station_lon,
        observations=observations,
        station_id=station_id,
    )
