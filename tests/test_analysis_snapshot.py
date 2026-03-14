from __future__ import annotations

import json

import pandas as pd

from ogn_tool.models.rf_analysis_dataset import RFAnalysisDataset
from ogn_tool.models.rf_analysis_results import RFAnalysisResults
from ogn_tool.models.rf_observation_vector import RFObservationVector
from ogn_tool.runtime.analysis_snapshot import build_analysis_snapshot, write_analysis_snapshot


def test_build_analysis_snapshot_serializes_metrics() -> None:
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
        ),
        RFObservationVector(
            station_id="S2",
            aircraft_id="A2",
            lat=47.1,
            lon=7.1,
            altitude_m=1100.0,
            distance_km=12.0,
            bearing_deg=35.0,
            radio_horizon_km=130.0,
            timestamp=2,
            timestamp_ns=2,
        ),
    ]
    dataset = RFAnalysisDataset(observations=observations, results=RFAnalysisResults())
    network = {
        "metrics": {
            "network_summary": {
                "network_status": "WARNING",
                "single_station_ratio": 0.25,
            },
            "spof": pd.DataFrame(
                [
                    {
                        "station_id": "S1",
                        "spof_score": 4.5,
                        "coverage_loss_ratio": 0.3,
                        "aircraft_lost": 2,
                    }
                ]
            ),
            "coverage_gaps": pd.DataFrame(
                [
                    {
                        "lat": 47.2,
                        "lon": 7.2,
                        "station_count": 1,
                        "gap_level": "HIGH",
                        "notes": pd.NA,
                    }
                ]
            ),
        }
    }

    snapshot = build_analysis_snapshot(dataset, network)

    assert snapshot["snapshot_version"] == "1"
    assert "created_at" in snapshot
    assert snapshot["dataset_summary"]["observation_count"] == 2
    assert snapshot["dataset_summary"]["station_count"] == 2
    assert snapshot["dataset_summary"]["aircraft_count"] == 2
    assert isinstance(snapshot["network_metrics"], dict)
    assert isinstance(snapshot["network_metrics"]["spof"], list)
    assert snapshot["network_metrics"]["spof"][0]["station_id"] == "S1"
    assert snapshot["network_metrics"]["coverage_gaps"][0]["notes"] is None


def test_write_analysis_snapshot_persists_json(tmp_path) -> None:
    snapshot = {
        "snapshot_version": "1",
        "engine_version": "1.1",
        "created_at": "2026-03-14T12:00:00",
        "dataset_summary": {"observation_count": 1},
        "network_metrics": {"network_summary": {"network_status": "GOOD"}},
    }

    path = tmp_path / "analysis_snapshot.json"
    write_analysis_snapshot(snapshot, str(path))

    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["snapshot_version"] == "1"
    assert data["network_metrics"]["network_summary"]["network_status"] == "GOOD"
