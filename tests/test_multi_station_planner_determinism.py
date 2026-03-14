from __future__ import annotations

import pandas as pd

from ogn_tool.analysis.intelligence.multi_station_coverage import (
    build_candidate_station_aircraft_sets,
)
from ogn_tool.analysis.intelligence.multi_station_planner import (
    select_stations_greedy,
)



def test_multi_station_planner_deterministic_under_candidate_order() -> None:
    candidates = pd.DataFrame(
        [
            {"candidate_id": "A", "lat": 47.0, "lon": 7.0},
            {"candidate_id": "B", "lat": 47.1, "lon": 7.1},
            {"candidate_id": "C", "lat": 47.2, "lon": 7.2},
        ]
    )

    observations = pd.DataFrame(
        [
            {"lat": 47.0, "lon": 7.0, "aircraft_id": "x"},
            {"lat": 47.1, "lon": 7.1, "aircraft_id": "y"},
            {"lat": 47.2, "lon": 7.2, "aircraft_id": "z"},
        ]
    )

    shuffled = candidates.sample(frac=1, random_state=42)

    sets1 = build_candidate_station_aircraft_sets(candidates, observations)
    sets2 = build_candidate_station_aircraft_sets(shuffled, observations)

    result1, covered1 = select_stations_greedy(sets1, 2)
    result2, covered2 = select_stations_greedy(sets2, 2)

    assert result1 == result2
    assert covered1 == covered2



def test_multi_station_planner_result_stable_across_multiple_shuffles() -> None:
    candidates = pd.DataFrame(
        [
            {"candidate_id": f"C{i}", "lat": 47 + i * 0.01, "lon": 7 + i * 0.01}
            for i in range(10)
        ]
    )

    observations = pd.DataFrame(
        [
            {"lat": 47.05, "lon": 7.05, "aircraft_id": "A"},
            {"lat": 47.07, "lon": 7.07, "aircraft_id": "B"},
        ]
    )

    reference_result = None
    reference_covered = None

    for seed in range(10):
        shuffled = candidates.sample(frac=1, random_state=seed)
        station_sets = build_candidate_station_aircraft_sets(shuffled, observations)
        result, covered = select_stations_greedy(station_sets, 3)

        if reference_result is None:
            reference_result = result
            reference_covered = covered
        else:
            assert result == reference_result
            assert covered == reference_covered
