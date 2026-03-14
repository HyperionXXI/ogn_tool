from __future__ import annotations

from math import hypot
from typing import Any

from ogn_tool.models.scenario_result import ScenarioResult


GAP_DISTANCE_THRESHOLD = 0.05


def _distance(a: dict[str, Any], b: dict[str, Any]) -> float:
    return hypot(float(a["lat"]) - float(b["lat"]), float(a["lon"]) - float(b["lon"]))


def score_station_candidates(
    *,
    candidate_results: list[ScenarioResult],
    coverage_gaps: list[dict[str, float | int]] | None = None,
) -> list[ScenarioResult]:
    coverage_gaps = coverage_gaps or []

    for result in candidate_results:
        if not isinstance(result, ScenarioResult):
            continue

        metrics = result.metrics
        candidate = result.candidate or {}

        coverage_gain = metrics.get("coverage_gain", 0) or 0
        redundancy_gain = metrics.get("redundancy_gain", 0) or 0

        gap_bonus = 0
        if "lat" in candidate and "lon" in candidate:
            for gap in coverage_gaps:
                if not isinstance(gap, dict) or "lat" not in gap or "lon" not in gap:
                    continue
                if _distance(candidate, gap) < GAP_DISTANCE_THRESHOLD:
                    gap_bonus += 1

        metrics["priority_score"] = coverage_gain * 2 + redundancy_gain + gap_bonus

    return sorted(
        [result for result in candidate_results if isinstance(result, ScenarioResult)],
        key=lambda result: result.metrics.get("priority_score", 0),
        reverse=True,
    )


__all__ = ["score_station_candidates"]
