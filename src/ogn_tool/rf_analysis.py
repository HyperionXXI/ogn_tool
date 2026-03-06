# src/ogn_tool/rf_analysis.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass(frozen=True)
class AzimuthStats:
    angles_rad: np.ndarray
    max_distance_km: np.ndarray
    p90_distance_km: np.ndarray
    best_rssi_db: np.ndarray
    packet_count: np.ndarray


def bearing_deg(lat1: float, lon1: float, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    """Initial bearing from (lat1, lon1) to (lat2, lon2) in degrees [0, 360)."""
    lat1r = np.deg2rad(lat1)
    lon1r = np.deg2rad(lon1)
    lat2r = np.deg2rad(lat2.astype(float))
    lon2r = np.deg2rad(lon2.astype(float))
    dlon = lon2r - lon1r
    x = np.sin(dlon) * np.cos(lat2r)
    y = np.cos(lat1r) * np.sin(lat2r) - np.sin(lat1r) * np.cos(lat2r) * np.cos(dlon)
    brng = np.rad2deg(np.arctan2(x, y))
    return (brng + 360.0) % 360.0


def compute_azimuth_stats(
    station_lat: float,
    station_lon: float,
    lat: np.ndarray,
    lon: np.ndarray,
    max_distance_km: np.ndarray,
    best_rssi_db: np.ndarray | None,
    packet_count: np.ndarray | None,
    bin_size_deg: float = 5.0,
) -> AzimuthStats:
    az = bearing_deg(station_lat, station_lon, lat, lon)
    bins = (az // bin_size_deg).astype(int)
    n_bins = int(360 / bin_size_deg)

    max_bins = np.full(n_bins, np.nan, dtype=float)
    p90_bins = np.full(n_bins, np.nan, dtype=float)
    rssi_bins = np.full(n_bins, np.nan, dtype=float)
    count_bins = np.zeros(n_bins, dtype=float)

    for i in range(n_bins):
        idx = bins == i
        if not np.any(idx):
            continue
        vals = max_distance_km[idx]
        if vals.size:
            max_bins[i] = np.nanmax(vals)
            p90_bins[i] = np.nanpercentile(vals, 90)
        if best_rssi_db is not None:
            rssi_vals = best_rssi_db[idx]
            if rssi_vals.size:
                rssi_bins[i] = np.nanmax(rssi_vals)
        if packet_count is not None:
            count_bins[i] = float(np.nansum(packet_count[idx]))
        else:
            count_bins[i] = float(np.sum(idx))

    angles = np.deg2rad(np.arange(0, 360, bin_size_deg))
    return AzimuthStats(
        angles_rad=angles,
        max_distance_km=max_bins,
        p90_distance_km=p90_bins,
        best_rssi_db=rssi_bins,
        packet_count=count_bins,
    )


def compute_distance_probability(
    distance_km: np.ndarray,
    packet_count: np.ndarray,
    bin_size_km: float = 5.0,
) -> Tuple[np.ndarray, np.ndarray]:
    if distance_km.size == 0:
        return np.array([]), np.array([])
    max_d = float(np.nanmax(distance_km))
    bins = np.arange(0, max_d + bin_size_km, bin_size_km)
    centers = []
    probs = []
    for i in range(len(bins) - 1):
        low = bins[i]
        high = bins[i + 1]
        idx = (distance_km >= low) & (distance_km < high)
        if not np.any(idx):
            centers.append((low + high) / 2.0)
            probs.append(np.nan)
            continue
        active = np.sum(packet_count[idx] > 0)
        total = np.sum(idx)
        centers.append((low + high) / 2.0)
        probs.append(active / total if total else np.nan)
    return np.array(centers), np.array(probs)


def reliable_distance_km(
    centers_km: np.ndarray,
    probability: np.ndarray,
    threshold: float = 0.9,
) -> float:
    if centers_km.size == 0:
        return float("nan")
    idx = np.where(probability >= threshold)[0]
    if idx.size == 0:
        return float("nan")
    return float(np.nanmax(centers_km[idx]))
