from ogn_tool.domain.rf_analysis_dataset import RFAnalysisDataset
from ogn_tool.domain.rf_analysis_results import RFAnalysisResults
from ogn_tool.models.rf_observation_vector import RFObservationVector
from ogn_tool.pipeline.network_graph_stage import run_network_graph_stage


def test_shadow_metrics_exposed_in_results() -> None:
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
            station_id="S1",
            aircraft_id="A2",
            lat=47.1,
            lon=7.1,
            altitude_m=1100.0,
            distance_km=12.0,
            bearing_deg=120.0,
            radio_horizon_km=120.0,
            timestamp=2,
            timestamp_ns=2,
        ),
    ]

    dataset = RFAnalysisDataset(observations=observations, results=RFAnalysisResults())

    metrics = run_network_graph_stage(dataset)["metrics"]

    assert "station_angular_entropy" in metrics
    assert "shadow_risk_scores" in metrics
    assert isinstance(metrics["station_angular_entropy"], dict)
    assert isinstance(metrics["shadow_risk_scores"], dict)
    assert "S1" in metrics["station_angular_entropy"]
    assert "S1" in metrics["shadow_risk_scores"]
