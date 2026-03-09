"""
RF feature module: antenna diagnostics.
See docs/rf_features/06_antenna_diagnostics.md
"""

from __future__ import annotations

from typing import Any, Dict

import numpy as np
import pandas as pd


def _bearing_deg(lat1: float, lon1: float, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    lat1_r = np.radians(lat1)
    lon1_r = np.radians(lon1)
    lat2_r = np.radians(lat2)
    lon2_r = np.radians(lon2)
    dlon = lon2_r - lon1_r
    y = np.sin(dlon) * np.cos(lat2_r)
    x = np.cos(lat1_r) * np.sin(lat2_r) - np.sin(lat1_r) * np.cos(lat2_r) * np.cos(dlon)
    brng = np.degrees(np.arctan2(y, x))
    return (brng + 360.0) % 360.0


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


def analyze(
    df_grid: pd.DataFrame,
    station_lat: float | None = None,
    station_lon: float | None = None,
    **_: Any,
) -> Dict[str, Any]:
    if df_grid is None or df_grid.empty or station_lat is None or station_lon is None:
        return {"implemented": False, "summary": {}, "data": None}

    lat = pd.to_numeric(df_grid.get("lat"), errors="coerce").to_numpy()
    lon = pd.to_numeric(df_grid.get("lon"), errors="coerce").to_numpy()
    pkt = pd.to_numeric(df_grid.get("packet_count"), errors="coerce").to_numpy()
    dist = pd.to_numeric(df_grid.get("max_distance_km"), errors="coerce").to_numpy()
    rssi = pd.to_numeric(df_grid.get("best_rssi_db"), errors="coerce").to_numpy()

    mask = np.isfinite(lat) & np.isfinite(lon) & np.isfinite(pkt) & np.isfinite(dist)
    if not mask.any():
        return {"implemented": False, "summary": {}, "data": None}

    lat = lat[mask]
    lon = lon[mask]
    pkt = pkt[mask]
    dist = dist[mask]
    rssi = rssi[mask]

    az = _bearing_deg(float(station_lat), float(station_lon), lat, lon)
    bin_size = 30.0
    bins = (az // bin_size).astype(int)
    centers = bins * bin_size + (bin_size / 2.0)

    df = pd.DataFrame(
        {
            "azimuth_bin": bins,
            "azimuth_center_deg": centers,
            "packet_count": pkt,
            "max_distance_km": dist,
            "best_rssi_db": rssi,
        }
    )

    agg = (
        df.groupby("azimuth_bin", as_index=False)
        .agg(
            azimuth_center_deg=("azimuth_center_deg", "mean"),
            packet_count=("packet_count", "sum"),
            max_distance_km=("max_distance_km", "max"),
            mean_distance_km=("max_distance_km", "mean"),
            p95_distance_km=("max_distance_km", lambda x: _weighted_percentile(x.to_numpy(), np.ones_like(x), 0.95)),
            mean_rssi_db=("best_rssi_db", "mean"),
        )
        .sort_values("azimuth_bin")
    )

    packet_total = float(np.nansum(agg["packet_count"])) if not agg.empty else 0.0
    min_packets = max(2000.0, 0.02 * packet_total) if packet_total else 0.0
    valid = agg["packet_count"] >= min_packets
    valid_sectors = agg[valid]

    if valid_sectors.shape[0] < 5:
        return {"implemented": False, "summary": {}, "data": agg}

    p95 = pd.to_numeric(valid_sectors["p95_distance_km"], errors="coerce")
    pkt_valid = pd.to_numeric(valid_sectors["packet_count"], errors="coerce")
    p95 = p95[np.isfinite(p95)]
    pkt_valid = pkt_valid[np.isfinite(pkt_valid)]

    if p95.empty or pkt_valid.empty:
        return {"implemented": False, "summary": {}, "data": agg}

    best_idx = valid_sectors["p95_distance_km"].idxmax()
    worst_idx = valid_sectors["p95_distance_km"].idxmin()
    best_sector_deg = float(valid_sectors.loc[best_idx, "azimuth_center_deg"])
    worst_sector_deg = float(valid_sectors.loc[worst_idx, "azimuth_center_deg"])

    p95_max = float(valid_sectors["p95_distance_km"].max())
    p95_min = float(valid_sectors["p95_distance_km"].min())
    anisotropy_ratio = float(p95_max / max(p95_min, 1e-6))

    traffic_ratio = float(valid_sectors["packet_count"].max() / max(valid_sectors["packet_count"].min(), 1e-6))

    # Thresholds (simple, documented):
    # anisotropy < 1.5 -> GOOD; < 2.5 -> FAIR; >= 2.5 -> POOR
    if anisotropy_ratio < 1.5:
        health_status = "GOOD"
    elif anisotropy_ratio < 2.5:
        health_status = "FAIR"
    else:
        health_status = "POOR"

    suspected_shadow = bool(anisotropy_ratio >= 2.0)

    return {
        "implemented": True,
        "summary": {
            "sector_count": int(valid_sectors.shape[0]),
            "best_sector_deg": best_sector_deg,
            "worst_sector_deg": worst_sector_deg,
            "anisotropy_ratio": anisotropy_ratio,
            "suspected_shadow": suspected_shadow,
            "health_status": health_status,
        },
        "data": agg,
    }
