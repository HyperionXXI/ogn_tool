from __future__ import annotations

import pandas as pd

from ogn_tool.kernel.observation_rows import observations_to_rows
from ogn_tool.domain.rf.observation_schema import (
    SHADOW_COLUMNS,
    SPATIAL_COLUMNS,
    VISIBILITY_COLUMNS,
)


def _observations_to_dataframe(observations) -> pd.DataFrame:
    if observations is None:
        return pd.DataFrame()

    if isinstance(observations, dict):
        vectors = observations.get("vectors")
        if vectors is not None and len(vectors) > 0:
            return pd.DataFrame(observations_to_rows(vectors))

        distance_df = observations.get("distance_df")
        return pd.DataFrame(distance_df).copy() if distance_df is not None else pd.DataFrame()

    if isinstance(observations, pd.DataFrame):
        return observations.copy()

    return pd.DataFrame(observations_to_rows(observations))


def build_spatial_observation_frame(observations) -> pd.DataFrame:
    """Build a canonical spatial observation frame for geospatial analysis.

    Returns
    -------
    pandas.DataFrame
        DataFrame with guaranteed columns:
        - station_id : object
        - lat : float
        - lon : float

        Rows with missing station or coordinates are removed.
    """
    df = _observations_to_dataframe(observations)
    if df.empty:
        return pd.DataFrame(columns=SPATIAL_COLUMNS)

    if "station_id" not in df.columns and "igate" in df.columns:
        df["station_id"] = df["igate"]

    for column in SPATIAL_COLUMNS:
        if column not in df.columns:
            df[column] = pd.NA

    df = df[SPATIAL_COLUMNS].copy()
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce").astype("float64")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce").astype("float64")
    df = df.dropna(subset=["station_id", "lat", "lon"])
    return df.reset_index(drop=True)


def build_visibility_observation_frame(observations) -> pd.DataFrame:
    """Build a canonical visibility frame for station-aircraft relationships.

    Returns
    -------
    pandas.DataFrame
        DataFrame with guaranteed columns:
        - src : object
        - igate : object

        Rows with missing aircraft or station ids are removed.
    """
    df = _observations_to_dataframe(observations)
    if df.empty:
        return pd.DataFrame(columns=VISIBILITY_COLUMNS)

    if "src" not in df.columns and "aircraft_id" in df.columns:
        df["src"] = df["aircraft_id"]
    if "igate" not in df.columns and "station_id" in df.columns:
        df["igate"] = df["station_id"]

    for column in VISIBILITY_COLUMNS:
        if column not in df.columns:
            df[column] = pd.NA

    return df[VISIBILITY_COLUMNS].dropna(subset=VISIBILITY_COLUMNS).copy()


def build_shadow_observation_frame(observations) -> pd.DataFrame:
    """Build a canonical directional observation frame for shadow analysis.

    Returns
    -------
    pandas.DataFrame
        DataFrame with guaranteed columns:
        - station_id : object
        - bearing_deg : object
        - lat : object
        - lon : object
        - station_lat : object
        - station_lon : object

        Missing directional fields are filled with ``pd.NA`` so the schema
        remains stable for downstream analysis.
    """
    df = _observations_to_dataframe(observations)
    if df.empty:
        return pd.DataFrame(columns=SHADOW_COLUMNS)

    if "station_id" not in df.columns and "igate" in df.columns:
        df["station_id"] = df["igate"]
    if "bearing_deg" not in df.columns and "bearing" in df.columns:
        df["bearing_deg"] = df["bearing"]

    if "station_id" not in df.columns:
        return pd.DataFrame(
            columns=SHADOW_COLUMNS
        )

    for column in SHADOW_COLUMNS[1:]:
        if column not in df.columns:
            df[column] = pd.NA

    return df[SHADOW_COLUMNS].copy()


__all__ = [
    "build_shadow_observation_frame",
    "build_spatial_observation_frame",
    "build_visibility_observation_frame",
]
