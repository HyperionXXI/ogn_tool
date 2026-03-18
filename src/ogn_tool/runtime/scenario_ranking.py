from __future__ import annotations

from ogn_tool.models.scenario_result import ScenarioResult
from ogn_tool.intelligence.scenario.station_addition_analysis import analyze_station_addition


def rank_station_addition_candidates(
    baseline_snapshot: dict[str, object],
    *,
    observations,
    candidates: list[dict[str, float]],
) -> list[ScenarioResult]:
    results: list[ScenarioResult] = []

    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue

        lat = candidate.get("lat")
        lon = candidate.get("lon")
        if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
            continue

        result = analyze_station_addition(
            baseline_snapshot,
            observations=observations,
            lat=float(lat),
            lon=float(lon),
        )
        results.append(result)

    return sorted(results, key=lambda result: result.priority_score(), reverse=True)


__all__ = ["rank_station_addition_candidates"]
