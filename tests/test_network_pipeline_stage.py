from ogn_tool.models.rf_analysis_dataset import RFAnalysisDataset
from ogn_tool.models.rf_analysis_results import RFAnalysisResults
from ogn_tool.models.rf_observation_vector import RFObservationVector
from ogn_tool.pipeline.network_graph_stage import run_network_graph_stage


def test_network_pipeline_stage_builds_outputs():
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
            timestamp=60,
            timestamp_ns=1,
        ),
        RFObservationVector(
            station_id="S2",
            aircraft_id="A1",
            lat=47.0,
            lon=7.0,
            altitude_m=1000.0,
            distance_km=12.0,
            bearing_deg=35.0,
            radio_horizon_km=120.0,
            timestamp=120,
            timestamp_ns=2,
        ),
    ]
    dataset = RFAnalysisDataset(observations=observations, results=RFAnalysisResults(coverage=None))

    network = run_network_graph_stage(dataset)

    assert network["graph"] is not None
    assert network["metrics"]["connectivity"]["station_count"] == 2
    assert "events" in network
    assert "anomalies" in network["events"]
