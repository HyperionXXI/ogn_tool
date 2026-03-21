from ogn_tool.kernel import network_graph_engine
from ogn_tool.models.rf_observation_vector import RFObservationVector


def test_network_graph_engine_builds_graph_result():
    observations = [
        RFObservationVector(
            station_id="S1", aircraft_id="A1", lat=47.0, lon=7.0, altitude_m=1000.0,
            distance_km=10.0, bearing_deg=45.0, radio_horizon_km=120.0, timestamp=1, timestamp_ns=100
        ),
        RFObservationVector(
            station_id="S2", aircraft_id="A1", lat=47.0, lon=7.0, altitude_m=1000.0,
            distance_km=12.0, bearing_deg=50.0, radio_horizon_km=120.0, timestamp=1, timestamp_ns=200
        ),
    ]
    result = network_graph_engine.build_graph(observations)
    assert result.graph["nodes"]
    assert result.metrics["connectivity"]["station_count"] == 2


def test_network_graph_engine_compute_metrics_passthrough():
    graph = {"nodes": [{"id": "S1", "type": "station"}], "edges": []}
    metrics = network_graph_engine.compute_network_metrics(graph)
    assert metrics["connectivity"]["station_count"] == 1
