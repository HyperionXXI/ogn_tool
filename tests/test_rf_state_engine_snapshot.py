from ogn_tool.analysis.streaming.rf_state_engine import RFStateEngine
from ogn_tool.models.rf_analysis_dataset import RFAnalysisDataset


def test_rf_state_engine_snapshot_returns_dataset():
    engine = RFStateEngine(station_coords={"S1": (47.0, 7.0, 500.0)})

    engine.ingest_packet(
        {
            "src": "A1",
            "igate": "S1",
            "ts_epoch": 1700000000,
            "ts_ns": 1700000000000000000,
            "lat": 47.1,
            "lon": 7.1,
            "alt": 1200.0,
        }
    )

    snapshot = engine.snapshot()

    assert isinstance(snapshot, RFAnalysisDataset)
    assert isinstance(snapshot.observations, list)
    assert len(snapshot.observations) == 1

    obs = snapshot.observations[0]
    assert obs.station_id == "S1"
    assert obs.aircraft_id == "A1"
    assert obs.timestamp == 1700000000
    assert obs.timestamp_ns == 1700000000000000000
