from __future__ import annotations

from typing import Any

from ogn_tool.analysis.intelligence import simulate_station_removal
from ogn_tool.models.scenario_result import ScenarioMetrics, ScenarioResult


def analyze_station_removal(
    baseline_snapshot: dict[str, object],
    *,
    station_id: str,
) -> ScenarioResult:
    if not isinstance(baseline_snapshot, dict):
        raise ValueError("baseline_snapshot must be a dict")

    analysis_run = baseline_snapshot.get("analysis_run", {})
    baseline_run_id = None
    if isinstance(analysis_run, dict):
        baseline_run_id = analysis_run.get("run_id")

    network_metrics = baseline_snapshot.get("network_metrics", {})
    if not isinstance(network_metrics, dict):
        network_metrics = {}

    simulation_result = simulate_station_removal(
        station_id=station_id,
        network_metrics=network_metrics,
    )

    if not isinstance(simulation_result, dict):
        simulation_result = {}

    scenario_metrics: dict[str, Any] = {
        "network_status_after_removal": simulation_result.get("network_status_after_removal"),
        "aircraft_lost": simulation_result.get("aircraft_lost", 0),
        "coverage_loss_ratio": simulation_result.get("coverage_loss_ratio", 0.0),
        "stations_becoming_critical": simulation_result.get("stations_becoming_critical", []),
    }

    anomalies: list[str] = []

    baseline_summary = network_metrics.get("network_summary", {})
    baseline_status = None
    if isinstance(baseline_summary, dict):
        baseline_status = baseline_summary.get("network_status")

    scenario_status = scenario_metrics["network_status_after_removal"]

    if (
        baseline_status is not None
        and scenario_status is not None
        and scenario_status != baseline_status
    ):
        anomalies.append("network status changed")

    coverage_loss = scenario_metrics.get("coverage_loss_ratio", 0.0)
    if isinstance(coverage_loss, (int, float)) and coverage_loss > 0.1:
        anomalies.append("coverage loss increased")

    critical = scenario_metrics.get("stations_becoming_critical", [])
    if isinstance(critical, list) and critical:
        anomalies.append("new critical stations detected")

    return ScenarioResult(
        baseline_run_id=baseline_run_id,
        scenario="station_removal",
        station_id=station_id,
        metrics=ScenarioMetrics(scenario_metrics),
        anomalies=anomalies,
    )


__all__ = ["analyze_station_removal"]
