from __future__ import annotations

import pandas as pd


def build_rf_grid(df: pd.DataFrame, cell_size: float = 0.05) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()
    df["grid_lat"] = (df["lat"] // cell_size) * cell_size
    df["grid_lon"] = (df["lon"] // cell_size) * cell_size

    grid = (
        df.groupby(["grid_lat", "grid_lon"])
        .agg(
            packets=("src", "count"),
            aircraft=("src", "nunique"),
            mean_distance=("distance_km", "mean"),
            max_distance=("distance_km", "max"),
        )
        .reset_index()
    )

    return grid
