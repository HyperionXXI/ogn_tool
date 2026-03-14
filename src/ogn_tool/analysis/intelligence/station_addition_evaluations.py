from __future__ import annotations

import pandas as pd

from ogn_tool.analysis.intelligence import simulate_station_addition
from ogn_tool.models.station_addition_evaluation import StationAdditionEvaluation


REQUIRED_OUTPUT_COLUMNS = {
    "lat",
    "lon",
    "aircraft_supported",
    "coverage_gain",
    "redundancy_gain",
    "priority_score",
}


def build_station_addition_evaluations(
    candidates: pd.DataFrame,
    observations: pd.DataFrame,
) -> list[StationAdditionEvaluation]:
    result_df = simulate_station_addition(candidates, observations)

    if not isinstance(result_df, pd.DataFrame):
        raise ValueError("simulate_station_addition must return a pandas DataFrame")
    if result_df.empty:
        return []

    missing = REQUIRED_OUTPUT_COLUMNS - set(result_df.columns)
    if missing:
        raise ValueError(
            f"simulate_station_addition output missing columns: {sorted(missing)}"
        )

    evaluations: list[StationAdditionEvaluation] = []
    for row in result_df.itertuples(index=False):
        evaluations.append(
            StationAdditionEvaluation(
                lat=float(row.lat),
                lon=float(row.lon),
                aircraft_supported=int(row.aircraft_supported),
                coverage_gain=int(row.coverage_gain),
                redundancy_gain=int(row.redundancy_gain),
                priority_score=int(row.priority_score),
            )
        )

    return evaluations


__all__ = ["build_station_addition_evaluations"]
