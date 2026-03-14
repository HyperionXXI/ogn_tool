from __future__ import annotations

from typing import Any

import pandas as pd

from ogn_tool.analysis.intelligence import simulate_station_addition
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

    result_df = simulate_station_addition(candidates, observations)
    metrics = _aggregate_multi_station_metrics(result_df)

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



def _aggregate_multi_station_metrics(result_df: pd.DataFrame) -> dict[str, Any]:
    if not isinstance(result_df, pd.DataFrame) or result_df.empty:
        return {
            "candidate_count": 0,
            "aircraft_supported": 0,
            "coverage_gain": 0,
            "redundancy_gain": 0,
            "priority_score": 0,
        }

    def _sum_column(name: str) -> int:
        if name not in result_df.columns:
            return 0
        values = pd.to_numeric(result_df[name], errors="coerce").fillna(0)
        return int(values.sum())

    return {
        "candidate_count": int(len(result_df)),
        "aircraft_supported": _sum_column("aircraft_supported"),
        "coverage_gain": _sum_column("coverage_gain"),
        "redundancy_gain": _sum_column("redundancy_gain"),
        "priority_score": _sum_column("priority_score"),
    }


__all__ = ["simulate_multi_station_addition"]
