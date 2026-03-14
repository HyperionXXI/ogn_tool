from __future__ import annotations

from typing import Any

import pandas as pd

from ogn_tool.analysis.intelligence.station_addition_evaluations import (
    build_station_addition_evaluations,
)
from ogn_tool.models.multi_station_scenario_result import MultiStationScenarioResult
from ogn_tool.models.scenario_result import ScenarioMetrics


REQUIRED_COLUMNS = {"lat", "lon"}


def simulate_multi_station_addition(
    baseline_snapshot: dict[str, object],
    *,
    observations: pd.DataFrame,
    candidate_positions: list[dict[str, float]],
) -> MultiStationScenarioResult:
    if not isinstance(baseline_snapshot, dict):
        raise ValueError("baseline_snapshot must be a dict")

    analysis_run = baseline_snapshot.get("analysis_run", {})
    baseline_run_id = analysis_run.get("run_id") if isinstance(analysis_run, dict) else None

    candidates = pd.DataFrame(candidate_positions)
    if not candidates.empty:
        missing = REQUIRED_COLUMNS - set(candidates.columns)
        if missing:
            raise ValueError(f"candidate_positions must contain columns: {sorted(missing)}")
        candidates = candidates[["lat", "lon"]].copy()
        candidates["lat"] = pd.to_numeric(candidates["lat"], errors="coerce")
        candidates["lon"] = pd.to_numeric(candidates["lon"], errors="coerce")
        candidates = candidates.dropna(subset=["lat", "lon"])
    else:
        candidates = pd.DataFrame(columns=["lat", "lon"])

    evaluations = build_station_addition_evaluations(candidates, observations)
    metrics = _aggregate_multi_station_metrics(evaluations)

    anomalies: list[str] = []
    if metrics.get("coverage_gain", 0) > 0:
        anomalies.append("multi-station coverage improved")
    if metrics.get("redundancy_gain", 0) > 0:
        anomalies.append("multi-station redundancy improved")

    normalized_candidates = [
        {"lat": float(row.lat), "lon": float(row.lon)}
        for row in candidates.itertuples(index=False)
    ]

    return MultiStationScenarioResult(
        baseline_run_id=baseline_run_id,
        scenario="multi_station_addition",
        candidates=normalized_candidates,
        metrics=ScenarioMetrics(metrics),
        anomalies=anomalies,
    )



def _aggregate_multi_station_metrics(evaluations) -> dict[str, Any]:
    if not evaluations:
        return {
            "candidate_count": 0,
            "aircraft_supported": 0,
            "coverage_gain": 0,
            "redundancy_gain": 0,
            "priority_score": 0,
        }

    return {
        "candidate_count": int(len(evaluations)),
        "aircraft_supported": int(sum(e.aircraft_supported for e in evaluations)),
        "coverage_gain": int(sum(e.coverage_gain for e in evaluations)),
        "redundancy_gain": int(sum(e.redundancy_gain for e in evaluations)),
        "priority_score": int(sum(e.priority_score for e in evaluations)),
    }


__all__ = ["simulate_multi_station_addition"]
