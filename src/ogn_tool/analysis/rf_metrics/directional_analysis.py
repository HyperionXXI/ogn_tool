from __future__ import annotations

from typing import Any

import pandas as pd

from ogn_tool.analysis.shadow import detect_rf_shadows
from ogn_tool.rf.azimuth import analyze_directional_balance, compute_azimuth_histogram


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
        shadow_map = detect_rf_shadows(
            packets_filtered,
            azimuth_histogram,
            directional_balance,
            station_lat=station_lat,
            station_lon=station_lon,
        )

    return {
        "azimuth_histogram": azimuth_histogram,
        "directional_balance": directional_balance,
        "shadow_map": shadow_map,
    }
