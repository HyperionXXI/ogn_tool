from __future__ import annotations

from ogn_tool.domain.rf.packets import deduplicate_packets
from ogn_tool.domain.rf.rf_observations import compute_distance
from ogn_tool.kernel.directional_diagnostics import _compute_shadow_proxy as compute_shadow_proxy
from ogn_tool.kernel.grid import build_rf_grid


def build_rf_dataset(df, station_lat, station_lon):
    df = deduplicate_packets(df)
    if df is None:
        return df, build_rf_grid(df)

    df = df.copy()
    distance = compute_distance(df, station_lat, station_lon)
    if distance is not None:
        df["distance_km"] = distance

    grid = build_rf_grid(df)
    grid = compute_shadow_proxy(grid)
    return df, grid
