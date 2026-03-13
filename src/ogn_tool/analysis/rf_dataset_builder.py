from __future__ import annotations

from .packets import deduplicate_packets
from .rf_metrics.rf_statistics import compute_distance
from .geo.grid import build_rf_grid
from .shadow import compute_shadow_proxy


def build_rf_dataset(df, station_lat, station_lon):
    df = deduplicate_packets(df)
    df = compute_distance(df, station_lat, station_lon)
    grid = build_rf_grid(df)
    grid = compute_shadow_proxy(grid)
    return df, grid

