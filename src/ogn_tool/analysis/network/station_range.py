"""
RF feature module: station range.
See docs/rf_features/05_station_range.md
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd


def _weighted_percentile(values: np.ndarray, weights: np.ndarray, q: float) -> float:
    if values.size == 0:
        return float("nan")
    order = np.argsort(values)
    v = values[order]
    w = weights[order]
    cum = np.cumsum(w)
    if cum[-1] <= 0:
        return float("nan")
    cutoff = q * cum[-1]
    return float(v[np.searchsorted(cum, cutoff, side="left")])


def analyze(df_grid: pd.DataFrame) -> Dict[str, Any]:
    if df_grid is None or df_grid.empty:
        return {
            "implemented": True,
            "summary": {
                "grid_cells": 0,
                "packet_total": 0,
                "max_distance_km": None,
                "p95_distance_km": None,
            },
            "data": None,
        }

    dist = pd.to_numeric(df_grid.get("max_distance_km"), errors="coerce").to_numpy()
    pkt = pd.to_numeric(df_grid.get("packet_count"), errors="coerce").to_numpy()
    mask = np.isfinite(dist) & np.isfinite(pkt)
    dist = dist[mask]
    pkt = pkt[mask]

    grid_cells = int(len(df_grid))
    packet_total = int(np.nansum(pkt)) if pkt.size else 0
    max_distance_km = float(np.nanmax(dist)) if dist.size else None
    p95_distance_km = _weighted_percentile(dist, pkt, 0.95) if dist.size else None

    return {
        "implemented": True,
        "summary": {
            "grid_cells": grid_cells,
            "packet_total": packet_total,
            "max_distance_km": max_distance_km,
            "p95_distance_km": p95_distance_km,
        },
        "data": {
            "distance_km": dist,
            "packet_count": pkt,
        },
    }
