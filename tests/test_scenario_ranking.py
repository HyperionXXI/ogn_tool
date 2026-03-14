from __future__ import annotations

import pandas as pd

from ogn_tool.runtime.scenario_ranking import rank_station_addition_candidates


def test_rank_station_addition_candidates_orders_by_priority(monkeypatch) -> None:
    baseline_snapshot = {"analysis_run": {"run_id": "run_a"}}
    observations = pd.DataFrame([
        {"lat": 47.0, "lon": 7.0, "station_id": "S1"},
    ])

    def fake_analyze_station_addition(baseline_snapshot, *, observations, lat, lon):
        priority_map = {
            (47.31, 7.28): 34,
            (47.29, 7.25): 29,
            (47.34, 7.20): 21,
        }
        score = priority_map[(lat, lon)]
        return {
            "baseline_run_id": "run_a",
            "scenario": "station_addition",
            "candidate": {"lat": lat, "lon": lon},
            "scenario_metrics": {
                "priority_score": score,
                "coverage_gain": score // 3,
                "redundancy_gain": score // 6,
                "aircraft_supported": score,
            },
            "anomalies": [],
        }

    monkeypatch.setattr(
        "ogn_tool.runtime.scenario_ranking.analyze_station_addition",
        fake_analyze_station_addition,
    )

    results = rank_station_addition_candidates(
        baseline_snapshot,
        observations=observations,
        candidates=[
            {"lat": 47.29, "lon": 7.25},
            {"lat": 47.34, "lon": 7.20},
            {"lat": 47.31, "lon": 7.28},
        ],
    )

    assert [r["scenario_metrics"]["priority_score"] for r in results] == [34, 29, 21]
    assert results[0]["candidate"] == {"lat": 47.31, "lon": 7.28}


def test_rank_station_addition_candidates_skips_invalid_candidates(monkeypatch) -> None:
    def fake_analyze_station_addition(baseline_snapshot, *, observations, lat, lon):
        return {
            "baseline_run_id": None,
            "scenario": "station_addition",
            "candidate": {"lat": lat, "lon": lon},
            "scenario_metrics": {"priority_score": 1},
            "anomalies": [],
        }

    monkeypatch.setattr(
        "ogn_tool.runtime.scenario_ranking.analyze_station_addition",
        fake_analyze_station_addition,
    )

    results = rank_station_addition_candidates(
        {},
        observations=[],
        candidates=[
            {"lat": 47.0, "lon": 7.0},
            {"lat": 47.0},
            "bad",
        ],
    )

    assert len(results) == 1
    assert results[0]["candidate"] == {"lat": 47.0, "lon": 7.0}
