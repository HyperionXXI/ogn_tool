from __future__ import annotations

from typing import Any

from ogn_tool.runtime.station_addition_analysis import analyze_station_addition


def rank_station_addition_candidates(
    baseline_snapshot: dict[str, object],
    *,
    observations,
    candidates: list[dict[str, float]],
) -> list[dict[str, object]]:
    results: list[dict[str, object]] = []

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

    def _priority(result: dict[str, object]) -> Any:
        metrics = result.get("scenario_metrics", {})
        if isinstance(metrics, dict):
            return metrics.get("priority_score", 0)
        return 0

    return sorted(results, key=_priority, reverse=True)


__all__ = ["rank_station_addition_candidates"]
