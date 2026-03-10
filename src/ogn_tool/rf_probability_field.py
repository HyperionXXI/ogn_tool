from __future__ import annotations

import numpy as np
import pandas as pd


def build_rf_grid(
    df_packets: pd.DataFrame,
    cell_size_deg: float = 0.01,
) -> pd.DataFrame:
    df = df_packets.copy()

    # If we don’t have positional data, nothing to build.
    if df.empty or not {"lat", "lon"}.issubset(df.columns):
        return pd.DataFrame(
            columns=[
                "lat",
                "lon",
                "cell_size_deg",
                "packets",
                "aircraft",
                "max_distance",
                "median_rssi",
            ]
        )

    df = df.dropna(subset=["lat", "lon"])
    if df.empty:
        return pd.DataFrame(
            columns=[
                "lat",
                "lon",
                "cell_size_deg",
                "packets",
                "aircraft",
                "max_distance",
                "median_rssi",
            ]
        )

    # grid index
    df["grid_x"] = (df["lon"] / cell_size_deg).astype(int)
    df["grid_y"] = (df["lat"] / cell_size_deg).astype(int)

    grouped = df.groupby(["grid_x", "grid_y"])

    aircraft_col = "aircraft_id" if "aircraft_id" in df.columns else "src"
    rssi_col = "rssi_db" if "rssi_db" in df.columns else None

    agg = {
        "packets": ("lat", "count"),
        "aircraft": (aircraft_col, "nunique"),
    }
    if "distance_km" in df.columns:
        agg["max_distance"] = ("distance_km", "max")
    if rssi_col:
        agg["median_rssi"] = (rssi_col, "median")

    grid = grouped.agg(**agg).reset_index()

    grid["lat"] = grid["grid_y"] * cell_size_deg
    grid["lon"] = grid["grid_x"] * cell_size_deg
    grid["cell_size_deg"] = float(cell_size_deg)

    if "max_distance" not in grid.columns:
        grid["max_distance"] = np.nan
    if "median_rssi" not in grid.columns:
        grid["median_rssi"] = np.nan

    return grid


def compute_reception_probability(grid: pd.DataFrame) -> pd.DataFrame:
    grid = grid.copy()
    if "packets" not in grid.columns:
        return grid

    max_packets = grid["packets"].max()
    if max_packets == 0:
        grid["probability"] = 0.0
    else:
        grid["probability"] = grid["packets"] / max_packets

    grid["sample_count"] = grid["packets"]
    grid["confidence"] = grid["probability"]

    return grid


def build_rf_probability_field(df_packets: pd.DataFrame) -> pd.DataFrame:
    grid = build_rf_grid(df_packets)
    grid = compute_reception_probability(grid)
    return grid
