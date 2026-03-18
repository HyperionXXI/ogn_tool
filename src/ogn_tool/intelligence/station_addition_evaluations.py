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

    candidate_ids = _resolve_candidate_ids(candidates, result_df)

    evaluations: list[StationAdditionEvaluation] = []
    for row, candidate_id in zip(result_df.itertuples(index=False), candidate_ids, strict=False):
        evaluations.append(
            StationAdditionEvaluation(
                candidate_id=candidate_id,
                lat=float(row.lat),
                lon=float(row.lon),
                aircraft_supported=int(row.aircraft_supported),
                coverage_gain=int(row.coverage_gain),
                redundancy_gain=int(row.redundancy_gain),
                priority_score=int(row.priority_score),
            )
        )

    return evaluations



def _resolve_candidate_ids(candidates: pd.DataFrame, result_df: pd.DataFrame) -> list[str]:
    if len(candidates) != len(result_df):
        raise ValueError("candidate/result row count mismatch in station addition evaluation builder")

    if "candidate_id" in candidates.columns:
        work = candidates[["candidate_id"]].copy()
        work["candidate_id"] = work["candidate_id"].astype("string")
        if work["candidate_id"].isna().any() or (work["candidate_id"].str.len() == 0).any():
            raise ValueError("candidate_id must be non-empty when provided")
        return [str(value) for value in work["candidate_id"].tolist()]

    return [
        _candidate_id_from_coordinates(lat, lon)
        for lat, lon in zip(result_df["lat"].tolist(), result_df["lon"].tolist(), strict=False)
    ]



def _candidate_id_from_coordinates(lat: object, lon: object) -> str:
    return f"cand_{float(lat):.5f}_{float(lon):.5f}"


__all__ = ["build_station_addition_evaluations"]
