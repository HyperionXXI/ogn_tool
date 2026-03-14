from __future__ import annotations

from typing import Any

import pandas as pd

from ogn_tool.analysis.intelligence.multi_station_coverage import (
    build_candidate_station_aircraft_sets,
    evaluate_multi_station_coverage,
)
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
    station_aircraft = build_candidate_station_aircraft_sets(candidates, observations)
    coverage = evaluate_multi_station_coverage(station_aircraft)
    metrics = _aggregate_multi_station_metrics(evaluations, coverage)

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



def _aggregate_multi_station_metrics(evaluations, coverage) -> dict[str, Any]:
    if not evaluations:
        return {
            "candidate_count": 0,
            "aircraft_supported": 0,
            "unique_aircraft_supported": 0,
            "coverage_gain": 0,
            "redundancy_gain": 0,
            "priority_score": 0,
            "total_station_aircraft": 0,
            "overlapping_aircraft": 0,
            "redundancy_factor": 0.0,
        }

    redundancy_gain = int(sum(e.redundancy_gain for e in evaluations))
    unique_aircraft_supported = int(coverage.unique_aircraft_supported)

    return {
        "candidate_count": int(len(evaluations)),
        "aircraft_supported": unique_aircraft_supported,
        "unique_aircraft_supported": unique_aircraft_supported,
        "coverage_gain": unique_aircraft_supported,
        "redundancy_gain": redundancy_gain,
        "priority_score": int(unique_aircraft_supported * 2 + redundancy_gain),
        "total_station_aircraft": int(coverage.total_station_aircraft),
        "overlapping_aircraft": int(coverage.overlapping_aircraft),
        "redundancy_factor": float(coverage.redundancy_factor),
    }


__all__ = ["simulate_multi_station_addition"]
