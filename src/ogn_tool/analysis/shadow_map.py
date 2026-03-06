"""
RF feature module: shadow zones.
See docs/rf_features/04_shadow_zones.md
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd


def analyze(context: Dict[str, Any]) -> Dict[str, Any]:
    df_packets = context.get("packets")
    station_callsign = context.get("station_callsign")
    cell_size_km = float(context.get("cell_size_km", 3.0))

    if df_packets is None or df_packets.empty or not station_callsign:
        return {
            "implemented": False,
            "summary": {},
            "data": None,
        }

    lat = pd.to_numeric(df_packets.get("lat"), errors="coerce")
    lon = pd.to_numeric(df_packets.get("lon"), errors="coerce")
    if lat is None or lon is None:
        return {
            "implemented": False,
            "summary": {},
            "data": None,
        }

    cell_size_deg = cell_size_km / 111.0
    valid = lat.notna() & lon.notna()
    if not valid.any():
        return {
            "implemented": False,
            "summary": {},
            "data": None,
        }

    lat = lat[valid]
    lon = lon[valid]
    df = pd.DataFrame({"lat": lat, "lon": lon})

    # Local RX detection: prefer igate column, fallback to raw contains callsign
    if "igate" in df_packets.columns:
        igate = df_packets.loc[valid, "igate"].astype(str)
        local_mask = igate.eq(station_callsign)
    elif "raw" in df_packets.columns:
        raw = df_packets.loc[valid, "raw"].astype(str)
        local_mask = raw.str.contains(f",{station_callsign}:", na=False)
    else:
        local_mask = pd.Series([False] * len(df), index=df.index)

    df["cell_x"] = np.floor(df["lon"].to_numpy() / cell_size_deg).astype(int)
    df["cell_y"] = np.floor(df["lat"].to_numpy() / cell_size_deg).astype(int)

    global_counts = (
        df.groupby(["cell_x", "cell_y"], as_index=False)
        .agg(
            grid_lat=("lat", "mean"),
            grid_lon=("lon", "mean"),
            aircraft_global=("lat", "size"),
        )
    )

    local_df = df[local_mask]
    if local_df.empty:
        merged = global_counts.copy()
        merged["aircraft_local"] = 0
    else:
        local_counts = (
            local_df.groupby(["cell_x", "cell_y"], as_index=False)
            .agg(aircraft_local=("lat", "size"))
        )
        merged = global_counts.merge(local_counts, on=["cell_x", "cell_y"], how="left")
        merged["aircraft_local"] = merged["aircraft_local"].fillna(0).astype(int)

    merged["reception_ratio"] = merged["aircraft_local"] / merged["aircraft_global"]

    # Ignore cells with too few global samples
    merged = merged[merged["aircraft_global"] >= 10].copy()
    if merged.empty:
        return {
            "implemented": True,
            "summary": {
                "cells_total": 0,
                "shadow_cells": 0,
                "coverage_mean": None,
            },
            "data": merged,
        }

    cells_total = int(len(merged))
    shadow_cells = int((merged["reception_ratio"] < 0.2).sum())
    coverage_mean = float(merged["reception_ratio"].mean())

    return {
        "implemented": True,
        "summary": {
            "cells_total": cells_total,
            "shadow_cells": shadow_cells,
            "coverage_mean": coverage_mean,
        },
        "data": merged[
            [
                "grid_lat",
                "grid_lon",
                "aircraft_global",
                "aircraft_local",
                "reception_ratio",
            ]
        ],
    }
