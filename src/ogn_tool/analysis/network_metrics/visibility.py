from __future__ import annotations

from collections.abc import Iterable

import pandas as pd

from .coverage_metrics import aircraft_redundancy
from .station_metrics import compute_station_overlap, station_aircraft_matrix, station_overlap


def _observations_to_visibility_frame(observations) -> pd.DataFrame:
    if observations is None:
        return pd.DataFrame(columns=["src", "igate"])
    if isinstance(observations, dict):
        vectors = observations.get("vectors")
        if vectors is not None and len(vectors) > 0:
            observations = vectors
        else:
            observations = observations.get("distance_df")
    if isinstance(observations, pd.DataFrame):
        df = observations.copy()
    elif isinstance(observations, Iterable) and not isinstance(observations, (str, bytes, dict)):
        rows = []
        for obs in observations:
            rows.append({
                "src": getattr(obs, "aircraft_id", None),
                "igate": getattr(obs, "station_id", None),
                "lat": getattr(obs, "lat", None),
                "lon": getattr(obs, "lon", None),
                "altitude_m": getattr(obs, "altitude_m", None),
            })
        df = pd.DataFrame(rows)
    else:
        df = pd.DataFrame(columns=["src", "igate"])

    if "src" not in df.columns and "aircraft_id" in df.columns:
        df["src"] = df["aircraft_id"]
    if "igate" not in df.columns and "station_id" in df.columns:
        df["igate"] = df["station_id"]
    for col in ["src", "igate"]:
        if col not in df.columns:
            df[col] = pd.NA
    return df


def build_visibility_matrix(observations) -> pd.DataFrame:
    df = _observations_to_visibility_frame(observations)
    return station_aircraft_matrix(df)


def compute_visibility_overlap(matrix_or_observations) -> pd.DataFrame:
    if isinstance(matrix_or_observations, pd.DataFrame) and {"src", "igate", "packets"}.issubset(matrix_or_observations.columns):
        return station_overlap(matrix_or_observations)
    df = _observations_to_visibility_frame(matrix_or_observations)
    if "event_key" in df.columns and "station_id" in df.columns:
        return compute_station_overlap(df)
    return station_overlap(build_visibility_matrix(df))


def compute_station_dependency(matrix_or_observations) -> pd.DataFrame:
    matrix = matrix_or_observations
    if not (isinstance(matrix, pd.DataFrame) and {"src", "igate", "packets"}.issubset(matrix.columns)):
        matrix = build_visibility_matrix(matrix_or_observations)
    if matrix is None or matrix.empty:
        return pd.DataFrame(columns=["aircraft_id", "station_count", "single_station", "critical_station_id"])

    station_counts = matrix.groupby("src")["igate"].nunique()
    critical_station = (
        matrix.groupby("src")["igate"]
        .agg(lambda values: values.iloc[0] if len(pd.unique(values)) == 1 else None)
    )
    dependency = pd.DataFrame({
        "aircraft_id": station_counts.index.astype(str),
        "station_count": station_counts.values.astype(int),
    })
    dependency["single_station"] = dependency["station_count"] <= 1
    dependency["critical_station_id"] = dependency["aircraft_id"].map(critical_station.to_dict())
    return dependency


def compute_visibility_redundancy(matrix_or_observations):
    matrix = matrix_or_observations
    if not (isinstance(matrix, pd.DataFrame) and {"src", "igate", "packets"}.issubset(matrix.columns)):
        matrix = build_visibility_matrix(matrix_or_observations)
    return aircraft_redundancy(matrix)


def compute_visibility_summary(matrix: pd.DataFrame, overlap: pd.DataFrame | None = None, dependency: pd.DataFrame | None = None) -> dict:
    if matrix is None or matrix.empty:
        return {
            "aircraft_count": 0,
            "station_count": 0,
            "mean_stations_per_aircraft": 0.0,
            "single_station_aircraft_count": 0,
            "single_station_ratio": 0.0,
            "max_overlap": 0.0,
            "mean_overlap": 0.0,
        }

    if dependency is None:
        dependency = compute_station_dependency(matrix)
    if overlap is None:
        overlap = compute_visibility_overlap(matrix)

    stations_per_aircraft = matrix.groupby("src")["igate"].nunique()
    single_station_count = int(dependency["single_station"].sum()) if not dependency.empty else 0
    aircraft_count = int(matrix["src"].nunique())
    station_count = int(matrix["igate"].nunique())

    max_overlap = 0.0
    mean_overlap = 0.0
    if overlap is not None and not overlap.empty:
        values = overlap.to_numpy().astype(float, copy=False)
        if values.size > 0:
            max_overlap = float(values.max())
            mean_overlap = float(values.mean())

    return {
        "aircraft_count": aircraft_count,
        "station_count": station_count,
        "mean_stations_per_aircraft": float(stations_per_aircraft.mean()) if not stations_per_aircraft.empty else 0.0,
        "single_station_aircraft_count": single_station_count,
        "single_station_ratio": float(single_station_count / aircraft_count) if aircraft_count else 0.0,
        "max_overlap": max_overlap,
        "mean_overlap": mean_overlap,
    }


def compute_visibility_metrics(observations) -> dict:
    matrix = build_visibility_matrix(observations)
    overlap = compute_visibility_overlap(matrix)
    dependency = compute_station_dependency(matrix)
    redundancy = compute_visibility_redundancy(matrix)
    summary = compute_visibility_summary(matrix, overlap=overlap, dependency=dependency)
    return {
        "matrix": matrix,
        "overlap": overlap,
        "dependency": dependency,
        "redundancy": redundancy,
        "summary": summary,
    }
