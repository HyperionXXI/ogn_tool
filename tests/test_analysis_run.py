from __future__ import annotations

from ogn_tool.domain.rf_analysis_dataset import RFAnalysisDataset
from ogn_tool.models.rf_analysis_results import RFAnalysisResults
from ogn_tool.models.rf_observation_vector import RFObservationVector
from ogn_tool.runtime.analysis_run import build_analysis_run


def test_build_analysis_run_includes_context() -> None:
    observations = [
        RFObservationVector(
            station_id="S1",
            aircraft_id="A1",
            lat=47.0,
            lon=7.0,
            altitude_m=1000.0,
            distance_km=10.0,
            bearing_deg=30.0,
            radio_horizon_km=120.0,
            timestamp=1,
            timestamp_ns=1,
        )
    ]
    dataset = RFAnalysisDataset(observations=observations, results=RFAnalysisResults())

    run = build_analysis_run(
        dataset,
        config_summary={
            "station_id": "FK50887",
            "time_window_hours": 12,
            "dataset_mode": "aprs_packets",
            "metrics_profile": "default",
        },
    )

    assert run.run_id.startswith("run_")
    assert run.created_at
    assert run.engine_version
    assert run.dataset_summary["observation_count"] == 1
    assert run.dataset_summary["station_count"] == 1
    assert run.dataset_summary["aircraft_count"] == 1
    assert run.config_summary["station_id"] == "FK50887"
