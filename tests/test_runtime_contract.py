from ogn_tool.models.rf_analysis_dataset import RFAnalysisDataset
from ogn_tool.models.rf_analysis_results import RFAnalysisResults
from ogn_tool.models.rf_observation_vector import RFObservationVector
from ogn_tool.pipeline.network_graph_stage import run_network_graph_stage


EXPECTED_KEYS = {
    "visibility",
    "station_influence",
    "station_anomalies",
    "network_robustness",
    "station_placement",
    "station_health",
    "station_dominance",
    "station_angular_entropy",
    "network_redundancy",
    "shadow_risk_scores",
    "network_summary",
    "station_dependency",
    "spof",
    "coverage_gaps",
    "coverage_gap_priorities",
    "station_redundancy_planner",
    "station_addition_simulation",
}


def test_runtime_metrics_contract() -> None:
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

    dataset = RFAnalysisDataset(
        observations=observations,
        results=RFAnalysisResults(),
    )

    network = run_network_graph_stage(dataset)
    metrics = network["metrics"]

    assert EXPECTED_KEYS.issubset(metrics.keys())
