import pandas as pd
import numpy as np


def detect_rf_blind_zones(df: pd.DataFrame, grid_size=0.05):

    """
    Detect RF blind zones.

    A blind zone is defined as an area where aircraft are present
    but reception by stations is weak or absent.
    """

    df = df.copy()

    df["grid_lat"] = (df["lat"] / grid_size).round() * grid_size
    df["grid_lon"] = (df["lon"] / grid_size).round() * grid_size

    grid = (
        df.groupby(["grid_lat", "grid_lon"])
        .agg(
            aircraft=("src", "nunique"),
            stations=("igate", "nunique"),
            packets=("src", "count"),
        )
        .reset_index()
    )

    grid["blind_score"] = grid["aircraft"] / (grid["stations"] + 1)

    grid["blind_zone"] = grid["blind_score"] > 3

    return grid
