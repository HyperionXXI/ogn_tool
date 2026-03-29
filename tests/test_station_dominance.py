import pandas as pd

from ogn_tool.intelligence.station_dominance import compute_station_dominance


def test_compute_station_dominance_counts_unique_and_shared_aircraft() -> None:
    observations = pd.DataFrame(
        [
            {"src": "A1", "igate": "S1"},
            {"src": "A1", "igate": "S2"},
            {"src": "A2", "igate": "S1"},
        ]
    )

    result = compute_station_dominance(observations)

    by_station = result.set_index("station_id")
    assert int(by_station.loc["S1", "total_aircraft_count"]) == 2
    assert int(by_station.loc["S1", "unique_aircraft_count"]) == 1
    assert int(by_station.loc["S1", "shared_aircraft_count"]) == 1
    assert float(by_station.loc["S1", "dominance_ratio"]) == 0.5

    assert int(by_station.loc["S2", "total_aircraft_count"]) == 1
    assert int(by_station.loc["S2", "unique_aircraft_count"]) == 0
    assert int(by_station.loc["S2", "shared_aircraft_count"]) == 1
    assert float(by_station.loc["S2", "dominance_ratio"]) == 0.0


def test_compute_station_dominance_sorts_by_ratio_then_unique_aircraft() -> None:
    observations = pd.DataFrame(
        [
            {"src": "A1", "igate": "S1"},
            {"src": "A2", "igate": "S1"},
            {"src": "A2", "igate": "S2"},
            {"src": "A3", "igate": "S3"},
        ]
    )

    result = compute_station_dominance(observations)

    assert result["station_id"].tolist() == ["S3", "S1", "S2"]
    assert result["dominance_rank"].tolist() == [1, 2, 3]
