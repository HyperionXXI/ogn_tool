from __future__ import annotations

from ogn_tool.models.scenario_result import ScenarioMetrics, ScenarioResult
from ogn_tool.runtime.network_priority_scoring import score_station_candidates


def test_score_station_candidates_sorts_by_computed_priority() -> None:
    results = [
        ScenarioResult(
            baseline_run_id="run",
            scenario="station_addition",
            candidate={"lat": 47.31, "lon": 7.28},
            metrics=ScenarioMetrics({"coverage_gain": 3, "redundancy_gain": 1}),
            anomalies=[],
        ),
        ScenarioResult(
            baseline_run_id="run",
            scenario="station_addition",
            candidate={"lat": 47.35, "lon": 7.20},
            metrics=ScenarioMetrics({"coverage_gain": 6, "redundancy_gain": 0}),
            anomalies=[],
        ),
    ]

    ranked = score_station_candidates(candidate_results=results)

    assert [result.candidate for result in ranked] == [
        {"lat": 47.35, "lon": 7.2},
        {"lat": 47.31, "lon": 7.28},
    ]
    assert ranked[0].metrics["priority_score"] == 12
    assert ranked[1].metrics["priority_score"] == 7


def test_score_station_candidates_gap_proximity_increases_score() -> None:
    results = [
        ScenarioResult(
            baseline_run_id="run",
            scenario="station_addition",
            candidate={"lat": 47.30, "lon": 7.18},
            metrics=ScenarioMetrics({"coverage_gain": 1, "redundancy_gain": 1}),
            anomalies=[],
        ),
        ScenarioResult(
            baseline_run_id="run",
            scenario="station_addition",
            candidate={"lat": 48.00, "lon": 8.00},
            metrics=ScenarioMetrics({"coverage_gain": 1, "redundancy_gain": 1}),
            anomalies=[],
        ),
    ]

    ranked = score_station_candidates(
        candidate_results=results,
        coverage_gaps=[{"lat": 47.31, "lon": 7.19, "observation_count": 1}],
    )

    assert ranked[0].candidate == {"lat": 47.3, "lon": 7.18}
    assert ranked[0].metrics["priority_score"] == 4
    assert ranked[1].metrics["priority_score"] == 3


def test_score_station_candidates_ignores_invalid_gap_entries() -> None:
    results = [
        ScenarioResult(
            baseline_run_id="run",
            scenario="station_addition",
            candidate={"lat": 47.30, "lon": 7.18},
            metrics=ScenarioMetrics({"coverage_gain": 2, "redundancy_gain": 2}),
            anomalies=[],
        )
    ]

    ranked = score_station_candidates(
        candidate_results=results,
        coverage_gaps=[{"lat": 47.31}, "bad", None],
    )

    assert ranked[0].metrics["priority_score"] == 6
