from __future__ import annotations

import pandas as pd


def station_aircraft_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return dataframe with columns:
    src (aircraft), igate (station), packets
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["src", "igate", "packets"])
    return (
        df.groupby(["src", "igate"])
        .size()
        .reset_index(name="packets")
    )


def station_overlap(matrix: pd.DataFrame) -> pd.DataFrame:
    if matrix is None or matrix.empty:
        return pd.DataFrame()
    pivot = matrix.pivot(index="src", columns="igate", values="packets").fillna(0)
    overlap = pivot.T.dot(pivot)
    return overlap


def station_metrics(df: pd.DataFrame, station: str) -> dict:
    if df is None or df.empty or station is None:
        return {"aircraft": 0, "packets": 0, "max_distance": None, "mean_distance": None}
    sub = df[df["igate"] == station]
    return {
        "aircraft": int(sub["src"].nunique()) if "src" in sub.columns else 0,
        "packets": int(len(sub)),
        "max_distance": float(sub["distance_km"].max()) if "distance_km" in sub.columns and not sub.empty else None,
        "mean_distance": float(sub["distance_km"].mean()) if "distance_km" in sub.columns and not sub.empty else None,
    }


def aircraft_redundancy(matrix: pd.DataFrame) -> pd.Series:
    if matrix is None or matrix.empty:
        return pd.Series(dtype=int)
    counts = matrix.groupby("src")["igate"].nunique()
    return counts.value_counts().sort_index()
