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
    metrics = network["metrics"]

    assert network["graph"] is not None
    assert metrics["connectivity"]["station_count"] == 2
    assert "events" in network
    assert "anomalies" in network["events"]

    for key in [
        "station_health",
        "station_angular_entropy",
        "shadow_risk_scores",
        "network_summary",
        "station_dependency",
        "spof",
        "coverage_gaps",
        "coverage_gap_priorities",
        "station_redundancy_planner",
        "station_addition_simulation",
    ]:
        assert key in metrics

    assert not metrics["spof"].empty
    assert not metrics["coverage_gaps"].empty
    assert not metrics["coverage_gap_priorities"].empty
    assert not metrics["station_redundancy_planner"].empty
    assert not metrics["station_addition_simulation"].empty

    assert isinstance(metrics["station_angular_entropy"], dict)
    assert isinstance(metrics["shadow_risk_scores"], dict)
    assert metrics["station_angular_entropy"]
    assert metrics["shadow_risk_scores"]
