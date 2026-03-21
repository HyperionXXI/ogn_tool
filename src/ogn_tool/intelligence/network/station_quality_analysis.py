"""
RF feature module: station quality.
See docs/rf_features/10_station_quality.md
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd


def analyze(df_grid: pd.DataFrame) -> Dict[str, Any]:
    if df_grid is None or df_grid.empty:
        return {
            "implemented": True,
            "summary": {
                "packet_total": 0,
                "rssi_best": None,
                "rssi_mean": None,
                "quality_score": None,
            },
            "data": None,
        }

    rssi = pd.to_numeric(df_grid.get("best_rssi_db"), errors="coerce").to_numpy()
    pkt = pd.to_numeric(df_grid.get("packet_count"), errors="coerce").to_numpy()
    mask = np.isfinite(rssi) & np.isfinite(pkt)
    rssi = rssi[mask]
    pkt = pkt[mask]

    packet_total = int(np.nansum(pkt)) if pkt.size else 0
    rssi_best = float(np.nanmax(rssi)) if rssi.size else None
    rssi_mean = float(np.average(rssi, weights=pkt)) if rssi.size and np.nansum(pkt) > 0 else None

    quality_score = None
    if rssi_mean is not None:
        # Simple normalized score: -120 dB => 0, -60 dB => 100
        quality_score = float(max(0.0, min(100.0, (rssi_mean + 120.0) / 60.0 * 100.0)))

    return {
        "implemented": True,
        "summary": {
            "packet_total": packet_total,
            "rssi_best": rssi_best,
            "rssi_mean": rssi_mean,
            "quality_score": quality_score,
        },
        "data": {
            "rssi_db": rssi,
            "packet_count": pkt,
        },
    }
