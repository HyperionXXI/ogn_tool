"""
RF feature module: terrain analysis (heuristic).
See docs/rf_features/08_terrain_analysis.md
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
    if df_grid is None or not isinstance(df_grid, pd.DataFrame) or df_grid.empty or station_lat is None or station_lon is None:
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
            p95_distance_km=("max_distance_km", lambda x: _weighted_percentile(x.to_numpy(), np.ones_like(x), 0.95)),
            mean_rssi_db=("best_rssi_db", "mean"),
        )
        .sort_values("azimuth_bin")
    )

    packet_total = float(np.nansum(agg["packet_count"])) if not agg.empty else 0.0
    min_packets = max(2000.0, 0.02 * packet_total) if packet_total else 0.0
    valid = agg["packet_count"] >= min_packets
    valid_sectors = agg[valid].copy()

    if valid_sectors.shape[0] < 5:
        return {"implemented": False, "summary": {}, "data": agg}

    # Classification thresholds:
    # OPEN >= 200 km, MODERATE >= 120 km, LIMITED otherwise.
    def _classify(p95: float) -> str:
        if p95 >= 200:
            return "OPEN"
        if p95 >= 120:
            return "MODERATE"
        return "LIMITED"

    valid_sectors["terrain_class"] = valid_sectors["p95_distance_km"].apply(_classify)

    open_count = int((valid_sectors["terrain_class"] == "OPEN").sum())
    limited_count = int((valid_sectors["terrain_class"] == "LIMITED").sum())
    best_idx = valid_sectors["p95_distance_km"].idxmax()
    worst_idx = valid_sectors["p95_distance_km"].idxmin()
    best_opening_deg = float(valid_sectors.loc[best_idx, "azimuth_center_deg"])
    main_limited_deg = float(valid_sectors.loc[worst_idx, "azimuth_center_deg"])

    # Terrain mask suspected if 3 adjacent LIMITED sectors (circular).
    limited_bins = valid_sectors.loc[valid_sectors["terrain_class"] == "LIMITED", "azimuth_bin"].to_numpy()
    limited_set = set(int(x) for x in limited_bins)
    mask_suspected = False
    for b in limited_set:
        if ((b - 1) % 12) in limited_set and ((b + 1) % 12) in limited_set:
            mask_suspected = True
            break

    if open_count >= limited_count:
        terrain_status = "OPEN"
    elif limited_count >= open_count and limited_count >= 3:
        terrain_status = "CONSTRAINED"
    else:
        terrain_status = "MIXED"

    summary = {
        "sector_count": int(valid_sectors.shape[0]),
        "open_sector_count": open_count,
        "limited_sector_count": limited_count,
        "best_opening_deg": best_opening_deg,
        "main_limited_deg": main_limited_deg,
        "terrain_mask_suspected": bool(mask_suspected),
        "terrain_status": terrain_status,
    }

    return {"implemented": True, "summary": summary, "data": valid_sectors}
