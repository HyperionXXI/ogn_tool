from __future__ import annotations

import pandas as pd

from ogn_tool.models.scenario_result import ScenarioMetrics, ScenarioResult
from ogn_tool.runtime.station_candidate_search import search_station_candidates


def test_search_station_candidates_returns_top_k(monkeypatch) -> None:
    def fake_rank_station_addition_candidates(baseline_snapshot, *, observations, candidates):
        return [
            ScenarioResult(
                baseline_run_id="run_a",
                scenario="station_addition",
                candidate={"lat": 47.31, "lon": 7.28},
                metrics=ScenarioMetrics({"priority_score": 34}),
                anomalies=[],
            ),
            ScenarioResult(
                baseline_run_id="run_a",
                scenario="station_addition",
                candidate={"lat": 47.29, "lon": 7.25},
                metrics=ScenarioMetrics({"priority_score": 29}),
                anomalies=[],
            ),
            ScenarioResult(
                baseline_run_id="run_a",
                scenario="station_addition",
                candidate={"lat": 47.34, "lon": 7.20},
                metrics=ScenarioMetrics({"priority_score": 21}),
                anomalies=[],
            ),
        ]

    monkeypatch.setattr(
        "ogn_tool.runtime.station_candidate_search.rank_station_addition_candidates",
        fake_rank_station_addition_candidates,
    )

    candidates = pd.DataFrame(
        [
            {"lat": 47.31, "lon": 7.28},
            {"lat": 47.29, "lon": 7.25},
            {"lat": 47.34, "lon": 7.20},
        ]
    )

    results = search_station_candidates(
        {},
        observations=[],
        candidates=candidates,
        top_k=2,
    )

    assert len(results) == 2
    assert results[0].candidate == {"lat": 47.31, "lon": 7.28}
    assert results[1].candidate == {"lat": 47.29, "lon": 7.25}


def test_search_station_candidates_normalizes_and_filters_invalid_rows(monkeypatch) -> None:
    captured = {}

    def fake_rank_station_addition_candidates(baseline_snapshot, *, observations, candidates):
        captured["candidates"] = candidates
        return []

    monkeypatch.setattr(
        "ogn_tool.runtime.station_candidate_search.rank_station_addition_candidates",
        fake_rank_station_addition_candidates,
    )

    candidates = pd.DataFrame(
        [
            {"lat": 47.31, "lon": 7.28},
            {"lat": "bad", "lon": 7.25},
            {"lat": 47.34, "lon": None},
        ]
    )

    results = search_station_candidates(
        {},
        observations=[],
        candidates=candidates,
        top_k=10,
    )

    assert results == []
    assert captured["candidates"] == [{"lat": 47.31, "lon": 7.28}]
