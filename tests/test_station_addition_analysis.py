from __future__ import annotations

import pandas as pd

from ogn_tool.models.scenario_result import ScenarioResult
from ogn_tool.models.station_addition_evaluation import StationAdditionEvaluation
from ogn_tool.runtime.station_addition_analysis import analyze_station_addition



def test_station_addition_analysis(monkeypatch) -> None:
    baseline_snapshot = {
        "analysis_run": {"run_id": "run_a"},
        "network_metrics": {
            "network_summary": {
                "network_status": "GOOD"
            }
        },
    }

    observations = pd.DataFrame(
        [
            {"lat": 47.0, "lon": 7.0, "station_id": "S1"},
        ]
    )

    def fake_build_station_addition_evaluations(candidates, observations):
        return [
            StationAdditionEvaluation(
                candidate_id="cand_47.31000_7.28000",
                lat=47.31,
                lon=7.28,
                aircraft_supported=10,
                coverage_gain=4,
                redundancy_gain=2,
                priority_score=6,
            )
        ]

    monkeypatch.setattr(
        "ogn_tool.runtime.station_addition_analysis.build_station_addition_evaluations",
        fake_build_station_addition_evaluations,
    )

    result = analyze_station_addition(
        baseline_snapshot,
        observations=observations,
        lat=47.31,
        lon=7.28,
    )

    assert isinstance(result, ScenarioResult)
    assert result.baseline_run_id == "run_a"
    assert result.scenario == "station_addition"
    assert result.candidate == {"lat": 47.31, "lon": 7.28}

    metrics = result.metrics
    assert metrics.get("aircraft_supported") == 10
    assert metrics.get("coverage_gain") == 4
    assert metrics.get("redundancy_gain") == 2
    assert metrics.get("priority_score") == 6

    assert "coverage improved" in result.anomalies
    assert "redundancy improved" in result.anomalies
    assert "high-priority candidate" in result.anomalies



def test_station_addition_analysis_defaults_when_no_evaluations(monkeypatch) -> None:
    monkeypatch.setattr(
        "ogn_tool.runtime.station_addition_analysis.build_station_addition_evaluations",
        lambda candidates, observations: [],
    )

    result = analyze_station_addition(
        {},
        observations=pd.DataFrame(),
        lat=47.31,
        lon=7.28,
    )

    assert result.metrics.get("coverage_gain") == 0
    assert result.metrics.get("priority_score") == 0
    assert result.anomalies == []
