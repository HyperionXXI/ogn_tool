"""
RF feature module: polar coverage.
See docs/rf_features/01_polar_coverage.md
"""

from __future__ import annotations

from typing import Any, Dict

import math
import os
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
    if df_grid is None or df_grid.empty:
        return {
            "implemented": False,
            "summary": {},
            "data": None,
        }

    if station_lat is None or station_lon is None:
        env_lat = os.getenv("OGN_STATION_LAT")
        env_lon = os.getenv("OGN_STATION_LON")
        if env_lat is not None and env_lon is not None:
            station_lat = float(env_lat)
            station_lon = float(env_lon)
    if station_lat is None or station_lon is None:
        return {
            "implemented": False,
            "summary": {},
            "data": None,
        }

    lat = pd.to_numeric(df_grid.get("lat"), errors="coerce").to_numpy()
    lon = pd.to_numeric(df_grid.get("lon"), errors="coerce").to_numpy()
    pkt = pd.to_numeric(df_grid.get("packet_count"), errors="coerce").to_numpy()
    dist = pd.to_numeric(df_grid.get("max_distance_km"), errors="coerce").to_numpy()
    rssi = pd.to_numeric(df_grid.get("best_rssi_db"), errors="coerce").to_numpy()

    mask = np.isfinite(lat) & np.isfinite(lon) & np.isfinite(pkt)
    if not mask.any():
        return {
            "implemented": True,
            "summary": {"bins": 0, "packet_total": 0},
            "data": None,
        }

    lat = lat[mask]
    lon = lon[mask]
    pkt = pkt[mask]
    dist = dist[mask]
    rssi = rssi[mask]

    az = _bearing_deg(station_lat, station_lon, lat, lon)
    bin_size = 15.0
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
            grid_cells=("packet_count", "size"),
            max_distance_km=("max_distance_km", "max"),
            p95_distance_km=("max_distance_km", lambda x: _weighted_percentile(x.to_numpy(), np.ones_like(x), 0.95)),
            best_rssi_db=("best_rssi_db", "max"),
            mean_rssi_db=("best_rssi_db", "mean"),
        )
        .sort_values("azimuth_bin")
    )

    # Weighted mean RSSI by packet_count where possible
    if "packet_count" in agg.columns and "mean_rssi_db" in agg.columns:
        pass

    # Normalize for a simple, explainable score:
    # score = 0.5 * distance_norm + 0.3 * rssi_norm + 0.2 * volume_norm
    # Each term is min-max normalized across sectors.
    def _norm(series: pd.Series) -> pd.Series:
        s = pd.to_numeric(series, errors="coerce")
        if s.notna().sum() == 0:
            return pd.Series([0.0] * len(s))
        vmin = s.min()
        vmax = s.max()
        if vmax == vmin:
            return pd.Series([1.0] * len(s))
        return (s - vmin) / (vmax - vmin)

    dist_norm = _norm(agg["max_distance_km"])
    rssi_norm = _norm(agg["best_rssi_db"])
    vol_norm = _norm(agg["packet_count"])
    agg["sector_score"] = 0.5 * dist_norm + 0.3 * rssi_norm + 0.2 * vol_norm

    packet_total = int(np.nansum(agg["packet_count"])) if not agg.empty else 0
    best_idx = agg["sector_score"].idxmax() if not agg.empty else None
    worst_idx = agg["sector_score"].idxmin() if not agg.empty else None
    best_sector_deg = float(agg.loc[best_idx, "azimuth_center_deg"]) if best_idx is not None else None
    worst_sector_deg = float(agg.loc[worst_idx, "azimuth_center_deg"]) if worst_idx is not None else None
    best_sector_score = float(agg.loc[best_idx, "sector_score"]) if best_idx is not None else None
    worst_sector_score = float(agg.loc[worst_idx, "sector_score"]) if worst_idx is not None else None
    max_distance_km = float(pd.to_numeric(agg["max_distance_km"], errors="coerce").max()) if not agg.empty else None

    anisotropy_ratio = None
    if best_sector_score is not None and worst_sector_score is not None:
        anisotropy_ratio = float(best_sector_score / max(worst_sector_score, 1e-6))

    shadow_suspect = False
    if worst_sector_score is not None and best_sector_score is not None:
        shadow_suspect = worst_sector_score < (0.5 * best_sector_score)

    return {
        "implemented": True,
        "summary": {
            "bins": int(agg["azimuth_bin"].nunique()),
            "packet_total": packet_total,
            "bin_size_deg": bin_size,
            "best_sector_deg": best_sector_deg,
            "worst_sector_deg": worst_sector_deg,
            "best_sector_score": best_sector_score,
            "worst_sector_score": worst_sector_score,
            "max_distance_km": max_distance_km,
            "anisotropy_ratio": anisotropy_ratio,
            "shadow_suspect": shadow_suspect,
        },
        "data": agg,
    }
