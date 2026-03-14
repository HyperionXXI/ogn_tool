from __future__ import annotations

import pandas as pd

from ogn_tool.analysis.intelligence.station_addition_evaluations import _candidate_id_from_coordinates
from ogn_tool.analysis.intelligence.station_addition_simulation import _distance_km
from ogn_tool.models.multi_station_coverage_evaluation import MultiStationCoverageEvaluation


REQUIRED_CANDIDATE_COLUMNS = {"lat", "lon"}


def build_candidate_station_aircraft_sets(
    candidates: pd.DataFrame,
    observations: pd.DataFrame,
    *,
    coverage_radius_km: float = 25.0,
) -> dict[str, set[str]]:
    if not isinstance(candidates, pd.DataFrame):
        raise ValueError("candidates must be a pandas DataFrame")
    if not isinstance(observations, pd.DataFrame):
        raise ValueError("observations must be a pandas DataFrame")

    missing_candidates = REQUIRED_CANDIDATE_COLUMNS - set(candidates.columns)
    if missing_candidates:
        raise ValueError(f"candidates must contain columns: {sorted(missing_candidates)}")

    aircraft_column = _resolve_aircraft_column(observations)
    work = observations[["lat", "lon", aircraft_column]].copy()
    work["lat"] = pd.to_numeric(work["lat"], errors="coerce")
    work["lon"] = pd.to_numeric(work["lon"], errors="coerce")
    work[aircraft_column] = work[aircraft_column].astype("string")
    work = work.dropna(subset=["lat", "lon", aircraft_column])

    station_aircraft: dict[str, set[str]] = {}

    selected_columns = ["lat", "lon"]
    if "candidate_id" in candidates.columns:
        selected_columns.append("candidate_id")
    normalized = candidates[selected_columns].copy()
    normalized["lat"] = pd.to_numeric(normalized["lat"], errors="coerce")
    normalized["lon"] = pd.to_numeric(normalized["lon"], errors="coerce")
    normalized = normalized.dropna(subset=["lat", "lon"])

    if "candidate_id" in normalized.columns:
        normalized["candidate_id"] = normalized["candidate_id"].astype("string")

    for candidate in normalized.itertuples(index=False):
        candidate_id = getattr(candidate, "candidate_id", None)
        has_candidate_id = candidate_id is not None and not pd.isna(candidate_id) and str(candidate_id) != ""
        station_id = str(candidate_id) if has_candidate_id else _candidate_id_from_coordinates(candidate.lat, candidate.lon)
        if work.empty:
            station_aircraft[station_id] = set()
            continue

        distances = _distance_km(
            float(candidate.lat),
            float(candidate.lon),
            work["lat"].to_numpy(),
            work["lon"].to_numpy(),
        )
        supported = work[distances <= coverage_radius_km]
        station_aircraft[station_id] = set(supported[aircraft_column].astype(str).tolist())

    return station_aircraft



def evaluate_multi_station_coverage(
    station_aircraft: dict[str, set[str]],
) -> MultiStationCoverageEvaluation:
    stations = sorted(station_aircraft.keys())

    union_aircraft: set[str] = set()
    total_station_aircraft = 0

    for aircraft_set in station_aircraft.values():
        total_station_aircraft += len(aircraft_set)
        union_aircraft |= aircraft_set

    unique_aircraft_supported = len(union_aircraft)
    overlapping_aircraft = total_station_aircraft - unique_aircraft_supported
    redundancy_factor = (
        unique_aircraft_supported / total_station_aircraft
        if total_station_aircraft > 0
        else 0.0
    )

    return MultiStationCoverageEvaluation(
        stations=stations,
        unique_aircraft_supported=unique_aircraft_supported,
        total_station_aircraft=total_station_aircraft,
        overlapping_aircraft=overlapping_aircraft,
        redundancy_factor=redundancy_factor,
    )



def _resolve_aircraft_column(observations: pd.DataFrame) -> str:
    for name in ("aircraft_id", "src", "aircraft"):
        if name in observations.columns:
            return name
    raise ValueError("observations must contain an aircraft identifier column")


__all__ = [
    "build_candidate_station_aircraft_sets",
    "evaluate_multi_station_coverage",
]
