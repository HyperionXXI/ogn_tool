from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def _observations_to_frame(observations) -> pd.DataFrame:
    if observations is None:
        return pd.DataFrame(columns=["station_id", "aircraft_id", "lat", "lon", "altitude_m"])
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
            rows.append(
                {
                    "station_id": getattr(obs, "station_id", None),
                    "aircraft_id": getattr(obs, "aircraft_id", None),
                    "lat": getattr(obs, "lat", None),
                    "lon": getattr(obs, "lon", None),
                    "altitude_m": getattr(obs, "altitude_m", None),
                }
            )
        df = pd.DataFrame(rows)
    else:
        df = pd.DataFrame(columns=["station_id", "aircraft_id", "lat", "lon", "altitude_m"])

    if "station_id" not in df.columns and "igate" in df.columns:
        df["station_id"] = df["igate"]
    if "aircraft_id" not in df.columns and "src" in df.columns:
        df["aircraft_id"] = df["src"]
    if "altitude_m" not in df.columns:
        if "altitude" in df.columns:
            df["altitude_m"] = df["altitude"]
        elif "alt" in df.columns:
            df["altitude_m"] = df["alt"]
        else:
            df["altitude_m"] = pd.NA
    for col in ["station_id", "aircraft_id", "lat", "lon", "altitude_m"]:
        if col not in df.columns:
            df[col] = pd.NA
    return df[["station_id", "aircraft_id", "lat", "lon", "altitude_m"]].copy()


def compute_station_aircraft_links(observations) -> pd.DataFrame:
    """
    Build station-to-aircraft reception links from RF observations.

    Returns one row per unique station/aircraft pair with an observation count.
    """

    df = _observations_to_frame(observations)
    if df.empty:
        return pd.DataFrame(
            columns=[
                "station_id",
                "aircraft_id",
                "observations",
                "aircraft_lat",
                "aircraft_lon",
                "aircraft_altitude_m",
            ]
        )

    df = df.dropna(subset=["station_id", "aircraft_id"])
    if df.empty:
        return pd.DataFrame(
            columns=[
                "station_id",
                "aircraft_id",
                "observations",
                "aircraft_lat",
                "aircraft_lon",
                "aircraft_altitude_m",
            ]
        )

    links = (
        df.groupby(["station_id", "aircraft_id"], dropna=False)
        .agg(
            observations=("aircraft_id", "size"),
            aircraft_lat=("lat", "median"),
            aircraft_lon=("lon", "median"),
            aircraft_altitude_m=("altitude_m", "median"),
        )
        .reset_index()
    )
    return links
