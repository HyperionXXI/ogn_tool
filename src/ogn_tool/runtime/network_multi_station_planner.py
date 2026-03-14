from __future__ import annotations

from itertools import combinations, islice

import pandas as pd

from ogn_tool.models.multi_station_scenario_result import MultiStationScenarioResult
from ogn_tool.models.scenario_result import ScenarioResult
from ogn_tool.runtime.network_multi_station_simulation import simulate_multi_station_addition


def plan_multi_station_additions(
    *,
    baseline_snapshot: dict,
    observations: pd.DataFrame,
    candidate_results: list[ScenarioResult],
    station_count: int = 2,
    top_n_candidates: int = 10,
    max_combinations: int = 200,
    top_k_solutions: int = 5,
) -> list[MultiStationScenarioResult]:
    if not isinstance(baseline_snapshot, dict):
        raise ValueError("baseline_snapshot must be a dict")
    if station_count < 1:
        raise ValueError("station_count must be >= 1")
    if top_n_candidates < 1:
        raise ValueError("top_n_candidates must be >= 1")
    if max_combinations < 1:
        raise ValueError("max_combinations must be >= 1")
    if top_k_solutions < 1:
        raise ValueError("top_k_solutions must be >= 1")

    valid_candidates = [
        result
        for result in candidate_results
        if isinstance(result, ScenarioResult)
        and isinstance(result.candidate, dict)
        and "lat" in result.candidate
        and "lon" in result.candidate
    ]

    sorted_candidates = sorted(
        valid_candidates,
        key=lambda result: result.metrics.get("priority_score") or 0,
        reverse=True,
    )
    selected_candidates = sorted_candidates[:top_n_candidates]

    solutions: list[MultiStationScenarioResult] = []
    for combo in islice(combinations(selected_candidates, station_count), max_combinations):
        positions = [result.candidate for result in combo if result.candidate is not None]
        solution = simulate_multi_station_addition(
            baseline_snapshot,
            observations=observations,
            candidate_positions=positions,
        )
        solutions.append(solution)

    solutions.sort(
        key=lambda result: result.metrics.get("priority_score") or 0,
        reverse=True,
    )
    return solutions[:top_k_solutions]


__all__ = ["plan_multi_station_additions"]
