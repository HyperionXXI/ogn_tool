from ogn_tool.analysis.network_graph.network_timeseries import (
    compute_station_activity_timeseries,
    compute_network_load_timeseries,
)
from ogn_tool.models.rf_observation_vector import RFObservationVector


def test_network_timeseries_station_activity():
    observations = [
        RFObservationVector("S1", "A1", 47.0, 7.0, 1000.0, 10.0, 30.0, 120.0, timestamp=60, timestamp_ns=1),
        RFObservationVector("S1", "A2", 47.1, 7.1, 1100.0, 11.0, 40.0, 120.0, timestamp=61, timestamp_ns=2),
    ]
    ts = compute_station_activity_timeseries(observations, bucket_seconds=60)
    assert len(ts) == 1
    assert int(ts.iloc[0]["observations"]) == 2


def test_network_timeseries_load():
    observations = [
        RFObservationVector("S1", "A1", 47.0, 7.0, 1000.0, 10.0, 30.0, 120.0, timestamp=60, timestamp_ns=1),
        RFObservationVector("S2", "A2", 47.1, 7.1, 1100.0, 11.0, 40.0, 120.0, timestamp=120, timestamp_ns=2),
    ]
    ts = compute_network_load_timeseries(observations, bucket_seconds=60)
    assert len(ts) == 2
