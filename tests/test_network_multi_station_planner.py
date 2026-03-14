from __future__ import annotations

import pandas as pd
import pytest

from ogn_tool.models.multi_station_scenario_result import MultiStationScenarioResult
from ogn_tool.models.scenario_result import ScenarioMetrics, ScenarioResult
from ogn_tool.runtime.network_multi_station_planner import plan_multi_station_additions


def test_plan_multi_station_additions_returns_top_ranked_solutions(monkeypatch) -> None:
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

    def fake_simulate_multi_station_addition(baseline_snapshot, *, observations, candidate_positions):
        score_map = {
            ((47.31, 7.28), (47.35, 7.20)): 50,
            ((47.31, 7.28), (47.29, 7.25)): 40,
            ((47.35, 7.20), (47.29, 7.25)): 30,
        }
        key = tuple((round(pos["lat"], 2), round(pos["lon"], 2)) for pos in candidate_positions)
        return MultiStationScenarioResult(
            baseline_run_id="run",
            scenario="multi_station_addition",
            candidates=candidate_positions,
            metrics=ScenarioMetrics({"priority_score": score_map[key]}),
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

    assert [result.metrics["priority_score"] for result in results] == [50, 40]



def test_plan_multi_station_additions_respects_max_combinations(monkeypatch) -> None:
    candidate_results = [
        ScenarioResult(
            baseline_run_id="run",
            scenario="station_addition",
            candidate={"lat": 47.30 + i, "lon": 7.20 + i},
            metrics=ScenarioMetrics({"priority_score": 10 - i}),
            anomalies=[],
        )
        for i in range(4)
    ]
    calls: list[list[dict[str, float]]] = []

    def fake_simulate_multi_station_addition(baseline_snapshot, *, observations, candidate_positions):
        calls.append(candidate_positions)
        return MultiStationScenarioResult(
            baseline_run_id="run",
            scenario="multi_station_addition",
            candidates=candidate_positions,
            metrics=ScenarioMetrics({"priority_score": len(candidate_positions)}),
            anomalies=[],
        )

    monkeypatch.setattr(
        "ogn_tool.runtime.network_multi_station_planner.simulate_multi_station_addition",
        fake_simulate_multi_station_addition,
    )

    plan_multi_station_additions(
        baseline_snapshot={},
        observations=pd.DataFrame(),
        candidate_results=candidate_results,
        station_count=2,
        top_n_candidates=4,
        max_combinations=2,
        top_k_solutions=5,
    )

    assert len(calls) == 2



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
