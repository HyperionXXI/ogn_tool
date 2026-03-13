from ogn_tool.analysis.intelligence.network_summary import compute_network_summary


def test_compute_network_summary_good():
    result = compute_network_summary(
        {
            "station_health": None,
            "visibility": {
                "summary": {
                    "single_station_ratio": 0.1,
                    "mean_stations_per_aircraft": 2.4,
                }
            },
        }
    )

    assert result["network_status"] == "GOOD"
    assert result["critical_station_count"] == 0
    assert result["warning_station_count"] == 0
    assert result["single_station_ratio"] == 0.1
    assert result["mean_stations_per_aircraft"] == 2.4



def test_compute_network_summary_degraded():
    import pandas as pd

    result = compute_network_summary(
        {
            "station_health": pd.DataFrame(
                [
                    {"station_id": "FK50887", "health_status": "CRITICAL", "impact_score": 6.1, "influence_score": 5.0},
                    {"station_id": "RAIMEUX", "health_status": "WARNING", "impact_score": 1.5, "influence_score": 2.0},
                ]
            ),
            "network_robustness": pd.DataFrame(
                [
                    {"station_id": "FK50887", "impact_score": 6.1},
                    {"station_id": "RAIMEUX", "impact_score": 1.5},
                ]
            ),
            "visibility": {
                "summary": {
                    "single_station_ratio": 0.5,
                    "mean_stations_per_aircraft": 1.3,
                }
            },
        }
    )

    assert result["network_status"] == "DEGRADED"
    assert result["critical_station_count"] == 1
    assert result["warning_station_count"] == 1
    assert result["top_critical_station"] == "FK50887"
