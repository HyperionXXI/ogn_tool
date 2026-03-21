from __future__ import annotations

import pandas as pd

from ogn_tool.kernel.multi_station_intelligence_facade import (
    build_candidate_station_aircraft_sets,
    select_stations_lazy_greedy,
)
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
    if not valid_candidates:
        return []

    sorted_candidates = sorted(
        valid_candidates,
        key=lambda result: result.metrics.get("priority_score") or 0,
        reverse=True,
    )
    selected_candidates = sorted_candidates[:top_n_candidates]

    candidate_lookup: dict[str, dict[str, float]] = {}
    candidate_rows = []
    for result in selected_candidates:
        candidate = result.candidate
        if candidate is None:
            continue
        candidate_id = _candidate_id_from_candidate(candidate)
        candidate_lookup[candidate_id] = candidate
        candidate_rows.append({"candidate_id": candidate_id, "lat": candidate["lat"], "lon": candidate["lon"]})

    if not candidate_rows:
        return []

    candidates_df = pd.DataFrame(candidate_rows)
    station_aircraft = build_candidate_station_aircraft_sets(candidates_df, observations)
    selected_station_ids, _ = select_stations_lazy_greedy(station_aircraft, station_count)

    positions = [candidate_lookup[station_id] for station_id in selected_station_ids if station_id in candidate_lookup]

    if not positions:
        return []

    solution = simulate_multi_station_addition(
        baseline_snapshot,
        observations=observations,
        candidate_positions=positions,
    )
    return [solution][:top_k_solutions]



def _candidate_id_from_candidate(candidate: dict[str, float]) -> str:
    return f"cand_{float(candidate['lat']):.5f}_{float(candidate['lon']):.5f}"


__all__ = ["plan_multi_station_additions"]
