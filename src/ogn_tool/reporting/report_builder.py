from __future__ import annotations

from typing import Any

from ogn_tool.models.scenario_result import ScenarioResult
from ogn_tool.reporting.report_models import NetworkEngineeringReport


def _scenario_result_to_dict(result: object) -> dict[str, Any]:
    if not isinstance(result, ScenarioResult):
        return {}

    metrics = result.metrics
    return {
        "station_id": result.station_id,
        "candidate": result.candidate,
        "coverage_loss_ratio": metrics.get("coverage_loss_ratio"),
        "stations_becoming_critical": metrics.get("stations_becoming_critical", []),
        "priority_score": metrics.get("priority_score"),
        "coverage_gain": metrics.get("coverage_gain"),
        "redundancy_gain": metrics.get("redundancy_gain"),
    }


def build_network_engineering_report(
    *,
    network_metrics: dict[str, object],
    coverage_gaps: list[dict[str, object]] | None = None,
    recommended_new_stations: list[object] | None = None,
    robustness_results: list[object] | None = None,
) -> NetworkEngineeringReport:
    coverage_gaps = coverage_gaps or []
    recommended_new_stations = recommended_new_stations or []
    robustness_results = robustness_results or []

    metrics = network_metrics if isinstance(network_metrics, dict) else {}
    summary = metrics.get("network_summary", {})
    if not isinstance(summary, dict):
        summary = {}

    station_health = metrics.get("station_health", [])
    if not isinstance(station_health, list):
        station_health = []

    critical_stations = [
        data for data in (_scenario_result_to_dict(result) for result in robustness_results) if data
    ]
    recommendations = [
        data for data in (_scenario_result_to_dict(result) for result in recommended_new_stations) if data
    ]

    return NetworkEngineeringReport(
        network_status=summary.get("network_status"),
        station_health=station_health,
        critical_stations=critical_stations,
        coverage_gaps=list(coverage_gaps),
        recommended_new_stations=recommendations,
    )


__all__ = ["build_network_engineering_report"]
