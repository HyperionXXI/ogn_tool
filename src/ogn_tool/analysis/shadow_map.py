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
    df_global = context.get("packets_global")
    if df_global is None:
        df_global = df_packets
    df_local = context.get("packets_local")
    if df_local is None:
        df_local = df_packets
    station_callsign = context.get("station_callsign")
    cell_size_km = float(context.get("cell_size_km", 3.0))
    window_hours = context.get("window_hours")

    if df_global is None or df_global.empty or not station_callsign:
        return {
            "implemented": False,
            "summary": {},
            "data": None,
        }

    lat = pd.to_numeric(df_global.get("lat"), errors="coerce")
    lon = pd.to_numeric(df_global.get("lon"), errors="coerce")
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

    # Local RX detection: match igate prefix or raw signature
    local_mask = pd.Series([False] * len(df), index=df.index)
    local_points_igate = 0
    local_points_raw = 0
    if df_local is not None and not df_local.empty:
        local_lat = pd.to_numeric(df_local.get("lat"), errors="coerce")
        local_lon = pd.to_numeric(df_local.get("lon"), errors="coerce")
        local_valid = local_lat.notna() & local_lon.notna()
        if "igate" in df_local.columns:
            igate = df_local.loc[local_valid, "igate"].astype(str)
            local_points = igate.eq(station_callsign) | igate.str.startswith(station_callsign)
            local_points_igate = int(local_points.sum())
        else:
            local_points = pd.Series([False] * int(local_valid.sum()))
        if "raw" in df_local.columns:
            raw = df_local.loc[local_valid, "raw"].astype(str)
            raw_match = raw.str.contains(f"qAS,{station_callsign}", na=False)
            local_points_raw = int(raw_match.sum())
            local_points = local_points | raw_match
        if local_valid.any():
            local_df = pd.DataFrame(
                {
                    "lat": local_lat[local_valid].to_numpy(),
                    "lon": local_lon[local_valid].to_numpy(),
                    "is_local": local_points.to_numpy(),
                }
            )
        else:
            local_df = pd.DataFrame(columns=["lat", "lon", "is_local"])
    else:
        local_df = pd.DataFrame(columns=["lat", "lon", "is_local"])

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

    global_points = int(len(df))
    local_points = int(local_df["is_local"].sum()) if "is_local" in local_df.columns else 0

    last_local_rx_ts = None
    if local_points > 0 and df_local is not None and not df_local.empty:
        if "ts_utc" in df_local.columns:
            try:
                last_local_rx_ts = str(df_local.loc[local_df["is_local"], "ts_utc"].max())
            except Exception:
                last_local_rx_ts = None
        if last_local_rx_ts is None and "ts_epoch" in df_local.columns:
            try:
                last_local_rx_ts = int(df_local.loc[local_df["is_local"], "ts_epoch"].max())
            except Exception:
                last_local_rx_ts = None

    local_df = local_df[local_df["is_local"]] if "is_local" in local_df.columns else pd.DataFrame()
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
                "global_points": global_points,
                "local_points": local_points,
                "local_points_igate": local_points_igate,
                "local_points_raw": local_points_raw,
                "usable_cells": 0,
            },
            "data": merged,
        }

    if local_points == 0:
        return {
            "implemented": False,
            "summary": {
                "reason": "no_local_packets_in_window",
                "global_points": global_points,
                "local_points": local_points,
                "selected_window_hours": window_hours,
                "last_local_rx_ts": last_local_rx_ts,
            },
            "data": None,
        }

    cells_total = int(len(merged))
    usable_cells = int(len(merged))
    shadow_cells = int((merged["reception_ratio"] < 0.2).sum())
    coverage_mean = float(merged["reception_ratio"].mean())

    return {
        "implemented": True,
        "summary": {
            "cells_total": cells_total,
            "shadow_cells": shadow_cells,
            "coverage_mean": coverage_mean,
            "global_points": global_points,
            "local_points": local_points,
            "local_points_igate": local_points_igate,
            "local_points_raw": local_points_raw,
            "usable_cells": usable_cells,
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
