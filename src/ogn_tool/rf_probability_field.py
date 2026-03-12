from __future__ import annotations

import numpy as np
import pandas as pd

from ogn_tool.analysis.grid import build_rf_grid as build_base_rf_grid


def build_rf_grid(
    df_packets: pd.DataFrame,
    cell_size_deg: float = 0.01,
) -> pd.DataFrame:
    if df_packets is None or df_packets.empty:
        return pd.DataFrame()

    # Canonical grid aggregation comes from analysis.grid.
    grid = build_base_rf_grid(df_packets, cell_size=float(cell_size_deg)).copy()
    if grid.empty:
        return grid

    # Normalize columns expected by probability-field consumers.
    if "grid_lat" in grid.columns and "lat" not in grid.columns:
        grid["lat"] = grid["grid_lat"]
    if "grid_lon" in grid.columns and "lon" not in grid.columns:
        grid["lon"] = grid["grid_lon"]

    grid["cell_size_deg"] = float(cell_size_deg)
    if "max_distance" not in grid.columns:
        if "max_distance_km" in grid.columns:
            grid["max_distance"] = pd.to_numeric(grid["max_distance_km"], errors="coerce")
        else:
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
