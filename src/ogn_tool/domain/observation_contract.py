from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping, Optional, Set

import pandas as pd


@dataclass(frozen=True)
class RFObservationsContract:
    """Lightweight structural summary of RF observations input.

    This does not enforce correctness of values, only the presence and basic
    shape of commonly used fields so that callers can reason about input
    quality in a uniform way.
    """

    has_vectors: bool
    has_distance_df: bool
    distance_df_columns: Set[str]
    has_station_coords: bool
    has_grid_for_analysis: bool


def _as_mapping(obj: Any) -> Optional[Mapping[str, Any]]:
    if isinstance(obj, Mapping):
        return obj
    return None


def _as_dataframe(obj: Any) -> Optional[pd.DataFrame]:
    if isinstance(obj, pd.DataFrame):
        return obj
    return None


def _is_vector_iterable(obj: Any) -> bool:
    """Return True for vector-like iterables, excluding DataFrames and mappings."""

    if isinstance(obj, (str, bytes)):
        return False
    if isinstance(obj, (Mapping, pd.DataFrame)):
        return False
    return isinstance(obj, Iterable)


def inspect_observations(observations: Any) -> RFObservationsContract:
    """Inspect an observations payload and return a structural summary.

    The function is deliberately permissive and never raises; unknown or
    unsupported shapes are reflected in the returned flags.
    """

    mapping = _as_mapping(observations)
    has_vectors = False
    has_distance_df = False
    distance_df_columns: Set[str] = set()
    has_station_coords = False
    has_grid_for_analysis = False

    if mapping is not None:
        vectors = mapping.get("vectors")
        if _is_vector_iterable(vectors):
            has_vectors = True

        distance_df = mapping.get("distance_df")
        df = _as_dataframe(distance_df)
        if df is not None:
            has_distance_df = True
            distance_df_columns = set(df.columns)

        has_station_coords = "station_lat" in mapping and "station_lon" in mapping

        grid_for_analysis = mapping.get("grid_for_analysis")
        has_grid_for_analysis = _as_dataframe(grid_for_analysis) is not None

    else:
        # Non-mapping payloads can still represent vectors directly.
        if _is_vector_iterable(observations):
            has_vectors = True

    return RFObservationsContract(
        has_vectors=has_vectors,
        has_distance_df=has_distance_df,
        distance_df_columns=distance_df_columns,
        has_station_coords=has_station_coords,
        has_grid_for_analysis=has_grid_for_analysis,
    )


def classify_observations(contract: RFObservationsContract) -> str:
    """Classify observations quality as 'valid', 'partial', or 'invalid'.

    The rules are intentionally conservative and non-breaking:
    - 'invalid': clearly unsupported shapes (no vectors and no distance_df).
    - 'valid': distance_df present with core RF columns, or vectors present.
    - 'partial': everything in between (some structure, but not fully
      matching the canonical expectations).
    """

    if not contract.has_vectors and not contract.has_distance_df:
        return "invalid"

    # For distance_df-based payloads, check for a minimal set of RF columns
    # that are commonly expected by feature matrix building and RF models.
    required_core = {"lat", "lon", "altitude_m"}
    if contract.has_distance_df and required_core.issubset(contract.distance_df_columns):
        return "valid"

    # Vectors alone, or distance_df without core columns, are considered partial:
    # structurally present but lacking strong guarantees.
    if contract.has_vectors or contract.has_distance_df:
        return "partial"

    return "invalid"


__all__ = ["RFObservationsContract", "inspect_observations", "classify_observations"]

