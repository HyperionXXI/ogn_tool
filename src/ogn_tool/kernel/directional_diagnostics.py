from __future__ import annotations

from typing import Any

import pandas as pd

from ogn_tool.kernel.rf.azimuth import analyze_directional_balance, compute_azimuth_histogram


def _compute_shadow_proxy(grid: pd.DataFrame, packets_threshold: int = 3) -> pd.DataFrame:
    if grid is None or grid.empty:
        return grid

    grid = grid.copy()
    grid["coverage"] = grid["packets"] > packets_threshold
    grid["shadow"] = ~grid["coverage"]
    return grid



def build_directional_diagnostics(
    packets_rf: pd.DataFrame,
    packets_filtered: pd.DataFrame,
    station_lat: float | None = None,
    station_lon: float | None = None,
) -> dict[str, Any]:
    azimuth_histogram = None
    directional_balance = None
    shadow_map = None

    if packets_rf is not None and not packets_rf.empty and "bearing_deg" in packets_rf.columns:
        azimuth_histogram = compute_azimuth_histogram(packets_rf["bearing_deg"])
        if azimuth_histogram is not None:
            directional_balance = analyze_directional_balance(azimuth_histogram)

    if (
        packets_filtered is not None
        and not packets_filtered.empty
        and azimuth_histogram is not None
        and directional_balance is not None
    ):
        if packets_filtered is None or len(packets_filtered) == 0:
            shadow_map = {"shadow_sectors": []}
        else:
            try:
                shadow_map = _compute_shadow_proxy(packets_filtered)
            except Exception:
                shadow_map = {"shadow_sectors": []}

    return {
        "azimuth_histogram": azimuth_histogram,
        "directional_balance": directional_balance,
        "shadow_map": shadow_map,
    }



def compute_shadow_proxy(grid: pd.DataFrame, packets_threshold: int = 3) -> pd.DataFrame:
    """
    Public wrapper for shadow proxy (debug / explanation use).
    """
    return _compute_shadow_proxy(grid, packets_threshold=packets_threshold)
