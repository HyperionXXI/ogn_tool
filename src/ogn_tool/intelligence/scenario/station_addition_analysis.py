from __future__ import annotations

from typing import Any

import pandas as pd

from ogn_tool.intelligence.station_addition_evaluations import (
    build_station_addition_evaluations,
)
from ogn_tool.models.scenario_result import ScenarioMetrics, ScenarioResult



def analyze_station_addition(
    baseline_snapshot: dict[str, object],
    *,
    observations,
    lat: float,
    lon: float,
) -> ScenarioResult:
    if not isinstance(baseline_snapshot, dict):
        raise ValueError("baseline_snapshot must be a dict")

    analysis_run = baseline_snapshot.get("analysis_run", {})
    baseline_run_id = (
        analysis_run.get("run_id")
        if isinstance(analysis_run, dict)
        else None
    )

    candidates = pd.DataFrame([
        {"lat": lat, "lon": lon}
    ])

    evaluations = build_station_addition_evaluations(
        candidates,
        observations,
    )
    evaluation = evaluations[0] if evaluations else None

    scenario_metrics: dict[str, Any] = {
        "aircraft_supported": evaluation.aircraft_supported if evaluation else 0,
        "coverage_gain": evaluation.coverage_gain if evaluation else 0,
        "redundancy_gain": evaluation.redundancy_gain if evaluation else 0,
        "priority_score": evaluation.priority_score if evaluation else 0,
    }

    anomalies: list[str] = []

    if scenario_metrics["coverage_gain"] > 0:
        anomalies.append("coverage improved")

    if scenario_metrics["redundancy_gain"] > 0:
        anomalies.append("redundancy improved")

    if scenario_metrics["priority_score"] > 0:
        anomalies.append("high-priority candidate")

    return ScenarioResult(
        baseline_run_id=baseline_run_id,
        scenario="station_addition",
        candidate={
            "lat": lat,
            "lon": lon,
        },
        metrics=ScenarioMetrics(scenario_metrics),
        anomalies=anomalies,
    )


__all__ = ["analyze_station_addition"]
