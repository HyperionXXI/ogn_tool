from ogn_tool.intelligence.station_removal_simulation import simulate_station_removal


def test_simulate_station_removal_empty():
    result = simulate_station_removal("S1", {})

    assert result["removed_station"] == "S1"
    assert result["aircraft_total"] == 0
    assert result["aircraft_lost"] == 0
    assert result["coverage_loss_ratio"] == 0.0
    assert result["network_status_after_removal"] == "GOOD"


def test_simulate_station_removal_counts_aircraft_lost_and_critical_stations():
    network_metrics = {
        "visibility": {
            "matrix": __import__("pandas").DataFrame(
                [
                    {"src": "A1", "igate": "S1", "packets": 5},
                    {"src": "A2", "igate": "S1", "packets": 4},
                    {"src": "A2", "igate": "S2", "packets": 3},
                    {"src": "A3", "igate": "S2", "packets": 2},
                    {"src": "A3", "igate": "S3", "packets": 1},
                ]
            )
        }
    }

    result = simulate_station_removal("S1", network_metrics)

    assert result["aircraft_total"] == 3
    assert result["aircraft_lost"] == 1
    assert result["coverage_loss_ratio"] == 1 / 3
    assert result["stations_becoming_critical"] == ["S2"]
    assert result["network_status_after_removal"] == "CRITICAL"


def test_simulate_station_removal_respects_max_aircraft():
    import pandas as pd

    network_metrics = {
        "visibility": {
            "matrix": pd.DataFrame(
                [
                    {"src": "A1", "igate": "S1", "packets": 1},
                    {"src": "A2", "igate": "S1", "packets": 1},
                    {"src": "A2", "igate": "S2", "packets": 1},
                    {"src": "A3", "igate": "S2", "packets": 1},
                ]
            )
        }
    }

    result = simulate_station_removal("S1", network_metrics, max_aircraft=2)

    assert result["aircraft_total"] == 2
    assert result["aircraft_lost"] == 1
