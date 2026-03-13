import pandas as pd

from ogn_tool.analysis.intelligence.station_dependency import compute_station_dependency


def test_compute_station_dependency_empty():
    result = compute_station_dependency({})
    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == [
        "station_id",
        "depends_on_station",
        "dependency_strength",
        "dependency_type",
        "notes",
    ]
    assert result.empty



def test_compute_station_dependency_detects_dominant_overlap():
    overlap = pd.DataFrame(
        [
            [10.0, 8.0, 2.0],
            [8.0, 12.0, 1.0],
            [2.0, 1.0, 9.0],
        ],
        index=["FK50887", "RAIMEUX", "LOW"],
        columns=["FK50887", "RAIMEUX", "LOW"],
    )
    influence = pd.DataFrame(
        [
            {"station_id": "FK50887", "influence_score": 5.0},
            {"station_id": "RAIMEUX", "influence_score": 4.0},
            {"station_id": "LOW", "influence_score": 1.0},
        ]
    )
    robustness = pd.DataFrame(
        [
            {"station_id": "FK50887", "impact_score": 5.0},
            {"station_id": "RAIMEUX", "impact_score": 3.0},
            {"station_id": "LOW", "impact_score": 0.5},
        ]
    )

    result = compute_station_dependency(
        {
            "visibility": {"overlap": overlap},
            "station_influence": influence,
            "network_robustness": robustness,
        }
    )

    fk = result[result["station_id"] == "FK50887"].iloc[0]
    low = result[result["station_id"] == "LOW"].iloc[0]

    assert fk["depends_on_station"] == "RAIMEUX"
    assert float(fk["dependency_strength"]) > 0.7
    assert fk["dependency_type"] == "overlap_dominance"

    assert low["depends_on_station"] == "FK50887"
