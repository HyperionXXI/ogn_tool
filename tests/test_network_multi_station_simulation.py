from __future__ import annotations

import pandas as pd
import pytest

from ogn_tool.models.multi_station_coverage_evaluation import MultiStationCoverageEvaluation
from ogn_tool.models.multi_station_scenario_result import MultiStationScenarioResult
from ogn_tool.models.station_addition_evaluation import StationAdditionEvaluation
from ogn_tool.runtime.network_multi_station_simulation import simulate_multi_station_addition



def test_simulate_multi_station_addition_uses_deduplicated_coverage(monkeypatch) -> None:
    baseline_snapshot = {"analysis_run": {"run_id": "run_a"}}
    observations = pd.DataFrame(
        [
            {"lat": 47.3, "lon": 7.2, "station_id": "S1", "aircraft_id": "A1"}
        ]
    )

    def fake_build_station_addition_evaluations(candidates, observations):
        assert list(candidates.columns) == ["lat", "lon"]
        return [
            StationAdditionEvaluation(
                candidate_id="cand_47.31000_7.28000",
                lat=47.31,
                lon=7.28,
                aircraft_supported=10,
                coverage_gain=4,
                redundancy_gain=2,
                priority_score=10,
            ),
            StationAdditionEvaluation(
                candidate_id="cand_47.35000_7.20000",
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
    monkeypatch.setattr(
        "ogn_tool.runtime.network_multi_station_simulation.build_candidate_station_aircraft_sets",
        lambda candidates, observations: {"candidate_1": {"A1", "A2", "A3"}, "candidate_2": {"A2", "A3", "A4"}},
    )
    monkeypatch.setattr(
        "ogn_tool.runtime.network_multi_station_simulation.evaluate_multi_station_coverage",
        lambda station_aircraft: MultiStationCoverageEvaluation(
            stations=["candidate_1", "candidate_2"],
            unique_aircraft_supported=4,
            total_station_aircraft=6,
            overlapping_aircraft=2,
            redundancy_factor=4 / 6,
        ),
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
    assert result.metrics["aircraft_supported"] == 4
    assert result.metrics["unique_aircraft_supported"] == 4
    assert result.metrics["coverage_gain"] == 4
    assert result.metrics["redundancy_gain"] == 3
    assert result.metrics["priority_score"] == 11
    assert result.metrics["total_station_aircraft"] == 6
    assert result.metrics["overlapping_aircraft"] == 2
    assert result.metrics["redundancy_factor"] == 4 / 6
    assert result.anomalies == [
        "multi-station coverage improved",
        "multi-station redundancy improved",
    ]



def test_simulate_multi_station_addition_filters_invalid_candidates(monkeypatch) -> None:
    observations = pd.DataFrame([{"lat": 47.3, "lon": 7.2, "station_id": "S1", "aircraft_id": "A1"}])
    captured: dict[str, object] = {}

    def fake_build_station_addition_evaluations(candidates, observations):
        captured["candidates"] = candidates.to_dict(orient="records")
        return []

    monkeypatch.setattr(
        "ogn_tool.runtime.network_multi_station_simulation.build_station_addition_evaluations",
        fake_build_station_addition_evaluations,
    )
    monkeypatch.setattr(
        "ogn_tool.runtime.network_multi_station_simulation.build_candidate_station_aircraft_sets",
        lambda candidates, observations: {},
    )
    monkeypatch.setattr(
        "ogn_tool.runtime.network_multi_station_simulation.evaluate_multi_station_coverage",
        lambda station_aircraft: MultiStationCoverageEvaluation(
            stations=[],
            unique_aircraft_supported=0,
            total_station_aircraft=0,
            overlapping_aircraft=0,
            redundancy_factor=0.0,
        ),
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
