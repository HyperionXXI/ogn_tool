from __future__ import annotations

from ogn_tool.analysis.intelligence.multi_station_coverage import (
    build_candidate_station_aircraft_sets,
    evaluate_multi_station_coverage,
)
from ogn_tool.models.multi_station_coverage_evaluation import MultiStationCoverageEvaluation



def test_deduplicated_coverage() -> None:
    station_aircraft = {
        "B": {"A2", "A3", "A4"},
        "A": {"A1", "A2", "A3"},
    }

    result = evaluate_multi_station_coverage(station_aircraft)

    assert result == MultiStationCoverageEvaluation(
        stations=["A", "B"],
        unique_aircraft_supported=4,
        total_station_aircraft=6,
        overlapping_aircraft=2,
        redundancy_factor=4 / 6,
    )



def test_build_candidate_station_aircraft_sets_uses_aircraft_union() -> None:
    candidates = __import__("pandas").DataFrame(
        [
            {"lat": 47.30, "lon": 7.20},
            {"lat": 47.50, "lon": 7.50},
        ]
    )
    observations = __import__("pandas").DataFrame(
        [
            {"lat": 47.30, "lon": 7.20, "aircraft_id": "A1"},
            {"lat": 47.31, "lon": 7.21, "aircraft_id": "A2"},
            {"lat": 47.50, "lon": 7.50, "aircraft_id": "A3"},
        ]
    )

    result = build_candidate_station_aircraft_sets(candidates, observations, coverage_radius_km=5.0)

    assert result == {
        "candidate_1": {"A1", "A2"},
        "candidate_2": {"A3"},
    }
