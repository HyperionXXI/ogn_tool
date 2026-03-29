import pandas as pd

from ogn_tool.intelligence.network_redundancy_score import compute_network_redundancy_score


def test_network_redundancy_score_fragile_network() -> None:
    metrics = {
        "visibility": {
            "summary": {
                "mean_stations_per_aircraft": 1.0,
                "single_station_ratio": 1.0,
            }
        },
        "station_dominance": pd.DataFrame(
            [
                {"station_id": "S1", "dominance_ratio": 1.0},
            ]
        ),
        "station_dependency": pd.DataFrame(
            [
                {"station_id": "S1", "dependency_strength": 1.0},
            ]
        ),
        "network_robustness": pd.DataFrame(),
    }

    result = compute_network_redundancy_score(metrics)

    assert result["redundancy_score"] < 0.3
    assert result["interpretation"] == "critical network"


def test_network_redundancy_score_redundant_network() -> None:
    metrics = {
        "visibility": {
            "summary": {
                "mean_stations_per_aircraft": 4.0,
                "single_station_ratio": 0.0,
            }
        },
        "station_dominance": pd.DataFrame(
            [
                {"station_id": "S1", "dominance_ratio": 0.05},
                {"station_id": "S2", "dominance_ratio": 0.10},
                {"station_id": "S3", "dominance_ratio": 0.15},
            ]
        ),
        "station_dependency": pd.DataFrame(
            [
                {"station_id": "S1", "dependency_strength": 0.1},
                {"station_id": "S2", "dependency_strength": 0.2},
                {"station_id": "S3", "dependency_strength": 0.3},
            ]
        ),
        "network_robustness": pd.DataFrame(),
    }

    result = compute_network_redundancy_score(metrics)

    assert result["redundancy_score"] > 0.8
    assert result["interpretation"] in {"good redundancy", "very high redundancy"}
