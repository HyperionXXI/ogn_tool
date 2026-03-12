from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


def _to_frame(observations) -> pd.DataFrame:
    if observations is None:
        return pd.DataFrame()
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
                "station_id": getattr(obs, "station_id", None),
                "aircraft_id": getattr(obs, "aircraft_id", None),
                "timestamp": getattr(obs, "timestamp", None),
                "timestamp_ns": getattr(obs, "timestamp_ns", None),
                "lat": getattr(obs, "lat", None),
                "lon": getattr(obs, "lon", None),
            })
        df = pd.DataFrame(rows)
    else:
        df = pd.DataFrame()
    if "station_id" not in df.columns and "igate" in df.columns:
        df["station_id"] = df["igate"]
    if "aircraft_id" not in df.columns and "src" in df.columns:
        df["aircraft_id"] = df["src"]
    if "timestamp" not in df.columns and "ts_epoch" in df.columns:
        df["timestamp"] = pd.to_numeric(df["ts_epoch"], errors="coerce").astype("Int64")
    if "timestamp_ns" not in df.columns and "ts_ns" in df.columns:
        df["timestamp_ns"] = pd.to_numeric(df["ts_ns"], errors="coerce").astype("Int64")
    return df


def _bucket_seconds(df: pd.DataFrame, bucket_seconds: int = 60) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["time_bucket"])
    out = df.copy()
    ts = pd.to_numeric(out.get("timestamp"), errors="coerce")
    out["time_bucket"] = (ts // int(bucket_seconds)) * int(bucket_seconds)
    return out.dropna(subset=["time_bucket"])


def compute_station_activity_timeseries(observations, bucket_seconds: int = 60) -> pd.DataFrame:
    df = _bucket_seconds(_to_frame(observations), bucket_seconds=bucket_seconds)
    if df.empty or "station_id" not in df.columns:
        return pd.DataFrame(columns=["time_bucket", "station_id", "observations"])
    return df.groupby(["time_bucket", "station_id"]).size().reset_index(name="observations")


def compute_network_load_timeseries(observations, bucket_seconds: int = 60) -> pd.DataFrame:
    df = _bucket_seconds(_to_frame(observations), bucket_seconds=bucket_seconds)
    if df.empty:
        return pd.DataFrame(columns=["time_bucket", "observations", "stations", "aircraft"])
    return df.groupby("time_bucket").agg(
        observations=("time_bucket", "size"),
        stations=("station_id", "nunique") if "station_id" in df.columns else ("time_bucket", "size"),
        aircraft=("aircraft_id", "nunique") if "aircraft_id" in df.columns else ("time_bucket", "size"),
    ).reset_index()


def compute_coverage_timeseries(graph, bucket_seconds: int = 60) -> pd.DataFrame:
    observations = graph.get("observations") if isinstance(graph, dict) else None
    df = _bucket_seconds(_to_frame(observations), bucket_seconds=bucket_seconds)
    if df.empty or not {"lat", "lon"}.issubset(df.columns):
        return pd.DataFrame(columns=["time_bucket", "coverage_points"])
    return df.groupby("time_bucket").agg(coverage_points=("lat", "count")).reset_index()


__all__ = ["compute_station_activity_timeseries", "compute_network_load_timeseries", "compute_coverage_timeseries"]
