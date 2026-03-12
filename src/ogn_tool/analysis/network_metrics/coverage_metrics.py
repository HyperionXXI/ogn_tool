from __future__ import annotations

import pandas as pd


def aircraft_redundancy(matrix: pd.DataFrame) -> pd.Series:
    if matrix is None or matrix.empty:
        return pd.Series(dtype=int)
    counts = matrix.groupby("src")["igate"].nunique()
    return counts.value_counts().sort_index()


def detect_network_blind_zones(df, grid_size_km=5):
    """
    Detect areas where RF reception is missing.
    Basic placeholder implementation.
    """
    if df is None or len(df) == 0:
        return pd.DataFrame()

    if "lat" not in df or "lon" not in df:
        return pd.DataFrame()

    grid = (
        df.groupby([
            (df["lat"] // (grid_size_km / 111)),
            (df["lon"] // (grid_size_km / 111)),
        ])
        .size()
        .reset_index(name="packet_count")
    )

    return grid
