from __future__ import annotations

import pandas as pd
import pytest

from ogn_tool.models.multi_station_scenario_result import MultiStationScenarioResult
from ogn_tool.models.scenario_result import ScenarioMetrics, ScenarioResult
from ogn_tool.runtime.network_multi_station_planner import plan_multi_station_additions



def test_plan_multi_station_additions_uses_greedy_selected_solution(monkeypatch) -> None:
    candidate_results = [
        ScenarioResult(
            baseline_run_id="run",
            scenario="station_addition",
            candidate={"lat": 47.31, "lon": 7.28},
            metrics=ScenarioMetrics({"priority_score": 30}),
            anomalies=[],
        ),
        ScenarioResult(
            baseline_run_id="run",
            scenario="station_addition",
            candidate={"lat": 47.35, "lon": 7.20},
            metrics=ScenarioMetrics({"priority_score": 20}),
            anomalies=[],
        ),
        ScenarioResult(
            baseline_run_id="run",
            scenario="station_addition",
            candidate={"lat": 47.29, "lon": 7.25},
            metrics=ScenarioMetrics({"priority_score": 10}),
            anomalies=[],
        ),
    ]

    monkeypatch.setattr(
        "ogn_tool.runtime.network_multi_station_planner.build_candidate_station_aircraft_sets",
        lambda candidates, observations: {
            "candidate_1": {"a1", "a2", "a3"},
            "candidate_2": {"a2", "a3", "a4"},
            "candidate_3": {"a5", "a6"},
        },
    )

    captured: dict[str, object] = {}

    def fake_simulate_multi_station_addition(baseline_snapshot, *, observations, candidate_positions):
        captured["candidate_positions"] = candidate_positions
        return MultiStationScenarioResult(
            baseline_run_id="run",
            scenario="multi_station_addition",
            candidates=candidate_positions,
            metrics=ScenarioMetrics({"priority_score": 50}),
            anomalies=[],
        )

    monkeypatch.setattr(
        "ogn_tool.runtime.network_multi_station_planner.simulate_multi_station_addition",
        fake_simulate_multi_station_addition,
    )

    results = plan_multi_station_additions(
        baseline_snapshot={},
        observations=pd.DataFrame(),
        candidate_results=candidate_results,
        station_count=2,
        top_n_candidates=3,
        max_combinations=10,
        top_k_solutions=2,
    )

    assert len(results) == 1
    assert results[0].metrics["priority_score"] == 50
    assert captured["candidate_positions"] == [
        {"lat": 47.31, "lon": 7.28},
        {"lat": 47.29, "lon": 7.25},
    ]



def test_plan_multi_station_additions_returns_empty_when_no_valid_candidates() -> None:
    results = plan_multi_station_additions(
        baseline_snapshot={},
        observations=pd.DataFrame(),
        candidate_results=[ScenarioResult(baseline_run_id="run", scenario="station_addition")],
    )

    assert results == []



def test_plan_multi_station_additions_validates_parameters() -> None:
    with pytest.raises(ValueError):
        plan_multi_station_additions(
            baseline_snapshot=None,
            observations=pd.DataFrame(),
            candidate_results=[],
        )

    with pytest.raises(ValueError):
        plan_multi_station_additions(
            baseline_snapshot={},
            observations=pd.DataFrame(),
            candidate_results=[],
            station_count=0,
        )
