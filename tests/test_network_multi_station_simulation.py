from __future__ import annotations

import pandas as pd
import pytest

from ogn_tool.models.multi_station_scenario_result import MultiStationScenarioResult
from ogn_tool.models.station_addition_evaluation import StationAdditionEvaluation
from ogn_tool.runtime.network_multi_station_simulation import simulate_multi_station_addition



def test_simulate_multi_station_addition_aggregates_results(monkeypatch) -> None:
    baseline_snapshot = {"analysis_run": {"run_id": "run_a"}}
    observations = pd.DataFrame([{"lat": 47.3, "lon": 7.2, "station_id": "S1"}])

    def fake_build_station_addition_evaluations(candidates, observations):
        assert list(candidates.columns) == ["lat", "lon"]
        return [
            StationAdditionEvaluation(
                lat=47.31,
                lon=7.28,
                aircraft_supported=10,
                coverage_gain=4,
                redundancy_gain=2,
                priority_score=10,
            ),
            StationAdditionEvaluation(
                lat=47.35,
                lon=7.20,
                aircraft_supported=8,
                coverage_gain=3,
                redundancy_gain=1,
                priority_score=7,
            ),
        ]

    monkeypatch.setattr(
        "ogn_tool.runtime.network_multi_station_simulation.build_station_addition_evaluations",
        fake_build_station_addition_evaluations,
    )

    result = simulate_multi_station_addition(
        baseline_snapshot,
        observations=observations,
        candidate_positions=[
            {"lat": 47.31, "lon": 7.28},
            {"lat": 47.35, "lon": 7.20},
        ],
    )

    assert isinstance(result, MultiStationScenarioResult)
    assert result.baseline_run_id == "run_a"
    assert result.scenario == "multi_station_addition"
    assert result.candidates == [
        {"lat": 47.31, "lon": 7.28},
        {"lat": 47.35, "lon": 7.2},
    ]
    assert result.metrics["candidate_count"] == 2
    assert result.metrics["aircraft_supported"] == 18
    assert result.metrics["coverage_gain"] == 7
    assert result.metrics["redundancy_gain"] == 3
    assert result.metrics["priority_score"] == 17
    assert result.anomalies == [
        "multi-station coverage improved",
        "multi-station redundancy improved",
    ]



def test_simulate_multi_station_addition_filters_invalid_candidates(monkeypatch) -> None:
    observations = pd.DataFrame([{"lat": 47.3, "lon": 7.2, "station_id": "S1"}])
    captured: dict[str, object] = {}

    def fake_build_station_addition_evaluations(candidates, observations):
        captured["candidates"] = candidates.to_dict(orient="records")
        return []

    monkeypatch.setattr(
        "ogn_tool.runtime.network_multi_station_simulation.build_station_addition_evaluations",
        fake_build_station_addition_evaluations,
    )

    result = simulate_multi_station_addition(
        {},
        observations=observations,
        candidate_positions=[
            {"lat": 47.31, "lon": 7.28},
            {"lat": "bad", "lon": 7.20},
            {"lat": 47.35, "lon": None},
        ],
    )

    assert captured["candidates"] == [{"lat": 47.31, "lon": 7.28}]
    assert result.candidates == [{"lat": 47.31, "lon": 7.28}]
    assert result.metrics["candidate_count"] == 0



def test_simulate_multi_station_addition_requires_snapshot_dict() -> None:
    with pytest.raises(ValueError):
        simulate_multi_station_addition(
            None,
            observations=pd.DataFrame(),
            candidate_positions=[],
        )
