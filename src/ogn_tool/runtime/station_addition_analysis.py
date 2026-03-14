from __future__ import annotations

from typing import Any

import pandas as pd

from ogn_tool.analysis.intelligence import simulate_station_addition


def analyze_station_addition(
    baseline_snapshot: dict[str, object],
    *,
    observations,
    lat: float,
    lon: float,
) -> dict[str, object]:
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

    result_df = simulate_station_addition(
        candidates,
        observations,
    )

    row = result_df.iloc[0].to_dict() if not result_df.empty else {}

    scenario_metrics: dict[str, Any] = {
        "aircraft_supported": row.get("aircraft_supported", 0),
        "coverage_gain": row.get("coverage_gain", 0),
        "redundancy_gain": row.get("redundancy_gain", 0),
        "priority_score": row.get("priority_score", 0),
    }

    anomalies: list[str] = []

    if scenario_metrics["coverage_gain"] > 0:
        anomalies.append("coverage improved")

    if scenario_metrics["redundancy_gain"] > 0:
        anomalies.append("redundancy improved")

    if scenario_metrics["priority_score"] > 0:
        anomalies.append("high-priority candidate")

    return {
        "baseline_run_id": baseline_run_id,
        "scenario": "station_addition",
        "candidate": {
            "lat": lat,
            "lon": lon,
        },
        "scenario_metrics": scenario_metrics,
        "anomalies": anomalies,
    }


__all__ = ["analyze_station_addition"]
