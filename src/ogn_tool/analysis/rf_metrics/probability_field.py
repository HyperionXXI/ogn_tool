from __future__ import annotations

import numpy as np
import pandas as pd

from ogn_tool.kernel.grid import build_rf_grid as build_base_rf_grid


def distance_decay(distance_km: pd.Series, gamma: float = 2.3, d0: float = 1.0) -> pd.Series:
    values = pd.to_numeric(distance_km, errors="coerce").clip(lower=1e-6)
    return np.power(float(d0) / values, float(gamma))


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

    if "packets" in grid.columns:
        packets = pd.to_numeric(grid["packets"], errors="coerce").fillna(0.0)
        max_packets = float(packets.max()) if len(packets) else 0.0
        if max_packets > 0:
            density = packets / max_packets
        else:
            density = pd.Series(0.0, index=grid.index, dtype=float)
    else:
        density = pd.Series(0.0, index=grid.index, dtype=float)

    if "max_distance" in grid.columns:
        decay = distance_decay(grid["max_distance"])
    else:
        decay = pd.Series(1.0, index=grid.index, dtype=float)

    probability = (density * decay).clip(lower=0.0, upper=1.0)

    grid["probability"] = probability
    grid["confidence"] = density.clip(lower=0.0, upper=1.0)
    grid["sample_count"] = pd.to_numeric(grid.get("packets", 0), errors="coerce").fillna(0).astype(int)

    return grid


def build_rf_probability_field(df_packets: pd.DataFrame) -> pd.DataFrame:
    grid = build_rf_grid(df_packets)
    grid = compute_reception_probability(grid)
    return grid
