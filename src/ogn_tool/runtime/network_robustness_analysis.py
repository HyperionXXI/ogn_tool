from __future__ import annotations

from ogn_tool.models.scenario_result import ScenarioResult
from ogn_tool.runtime.station_removal_analysis import analyze_station_removal


def analyze_network_robustness(
    baseline_snapshot: dict[str, object],
    *,
    station_ids: list[str],
) -> list[ScenarioResult]:
    if not isinstance(baseline_snapshot, dict):
        raise ValueError("baseline_snapshot must be a dict")

    results: list[ScenarioResult] = []

    for station_id in station_ids:
        if not isinstance(station_id, str) or not station_id:
            continue

        result = analyze_station_removal(
            baseline_snapshot,
            station_id=station_id,
        )
        if isinstance(result, ScenarioResult):
            results.append(result)

    results.sort(
        key=lambda result: (
            float(result.metrics.get("coverage_loss_ratio", 0)),
            len(result.metrics.get("stations_becoming_critical", []) or []),
        ),
        reverse=True,
    )

    return results


__all__ = ["analyze_network_robustness"]
