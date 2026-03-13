import pandas as pd

from ogn_tool.analysis.network_metrics.station_placement import compute_optimal_station_locations


def test_compute_optimal_station_locations_returns_sorted_dataframe():
    network_metrics = {
        "visibility": {
            "matrix": pd.DataFrame(
                [
                    {"src": "A1", "igate": "S1", "packets": 1, "lat": 47.00, "lon": 7.00},
                    {"src": "A2", "igate": "S1", "packets": 1, "lat": 47.02, "lon": 7.02},
                    {"src": "A2", "igate": "S2", "packets": 1, "lat": 47.02, "lon": 7.02},
                    {"src": "A3", "igate": "S2", "packets": 1, "lat": 47.20, "lon": 7.20},
                ]
            ),
            "dependency": pd.DataFrame(
                [
                    {"aircraft_id": "A1", "station_count": 1, "critical_station_id": "S1"},
                    {"aircraft_id": "A2", "station_count": 2, "critical_station_id": None},
                    {"aircraft_id": "A3", "station_count": 1, "critical_station_id": "S2"},
                ]
            ),
        },
        "station_influence": pd.DataFrame(
            [
                {"station_id": "S1", "aircraft_seen": 2, "lat": 47.00, "lon": 7.00},
                {"station_id": "S2", "aircraft_seen": 2, "lat": 47.20, "lon": 7.20},
            ]
        ),
        "network_robustness": pd.DataFrame(),
    }

    candidate_grid = pd.DataFrame(
        [
            {"lat": 47.01, "lon": 7.01},
            {"lat": 47.21, "lon": 7.21},
            {"lat": 48.00, "lon": 8.00},
        ]
    )

    placement = compute_optimal_station_locations(network_metrics, candidate_grid)

    assert not placement.empty
    assert set(placement.columns) >= {
        "lat",
        "lon",
        "coverage_gain",
        "redundancy_gain",
        "aircraft_supported",
        "critical_aircraft_supported",
        "nearest_station_distance_km",
        "placement_score",
    }
    assert placement["placement_score"].tolist() == sorted(placement["placement_score"].tolist(), reverse=True)
