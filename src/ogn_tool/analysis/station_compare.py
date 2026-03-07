"""
RF feature module: station comparison.
See docs/rf_features/09_station_comparison.md
"""

from __future__ import annotations

from typing import Any, Dict, Iterable

import numpy as np
import pandas as pd


def _haversine_km(lat1: float, lon1: float, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    r = 6371.0
    lat1_r = np.radians(lat1)
    lon1_r = np.radians(lon1)
    lat2_r = np.radians(lat2)
    lon2_r = np.radians(lon2)
    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1_r) * np.cos(lat2_r) * np.sin(dlon / 2.0) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return r * c


def _norm(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    if s.notna().sum() == 0:
        return pd.Series([0.0] * len(s), index=s.index)
    vmin = s.min()
    vmax = s.max()
    if vmax == vmin:
        return pd.Series([1.0] * len(s), index=s.index)
    return (s - vmin) / (vmax - vmin)


def analyze(
    df_packets: pd.DataFrame,
    station_coords: Dict[str, tuple[float, float]] | None = None,
    station_callsigns: Iterable[str] | None = None,
    **_: Any,
) -> Dict[str, Any]:
    if df_packets is None or not isinstance(df_packets, pd.DataFrame):
        return {"implemented": False, "summary": {"reason": "no_packets"}, "data": None}
    if df_packets.empty:
        return {"implemented": False, "summary": {"reason": "no_packets"}, "data": None}

    if station_coords is None:
        station_coords = {}
    stations = list(station_callsigns) if station_callsigns is not None else list(station_coords.keys())
    if len(stations) == 0:
        return {
            "implemented": False,
            "summary": {"reason": "missing_station_config", "configured_station_count": 0, "comparable_station_count": 0},
            "data": None,
        }
    if len(stations) < 2:
        return {
            "implemented": False,
            "summary": {
                "reason": "fewer_than_two_stations",
                "configured_station_count": len(stations),
                "comparable_station_count": 0,
            },
            "data": None,
        }

    df = df_packets.copy()
    for col in ("lat", "lon", "raw", "igate"):
        if col not in df.columns:
            return {"implemented": False, "summary": {}, "data": None}

    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df.dropna(subset=["lat", "lon"])
    if df.empty:
        return {"implemented": False, "summary": {}, "data": None}

    igate = df["igate"].fillna("").astype(str)
    raw = df["raw"].fillna("").astype(str)

    rows = []
    invalid_coords = 0
    for station in stations:
        if station not in station_coords:
            invalid_coords += 1
            continue
        st_lat, st_lon = station_coords[station]
        if st_lat is None or st_lon is None or not np.isfinite(st_lat) or not np.isfinite(st_lon):
            invalid_coords += 1
            continue
        mask = igate.str.startswith(station) | raw.str.contains(f"qAS,{station}", regex=False)
        sub = df.loc[mask]
        if sub.empty:
            continue
        dist = _haversine_km(float(st_lat), float(st_lon), sub["lat"].to_numpy(), sub["lon"].to_numpy())
        dist = dist[np.isfinite(dist) & (dist > 0)]
        if dist.size == 0:
            continue

        packet_total = int(len(dist))
        max_distance_km = float(np.max(dist))
        p95_distance_km = float(np.percentile(dist, 95))

        # Optional RSSI-based quality score (if available in raw)
        rssi = pd.to_numeric(
            sub["raw"].astype(str).str.extract(r"([0-9]+(?:\.[0-9]+)?)dB", expand=False),
            errors="coerce",
        ).to_numpy()
        rssi = rssi[np.isfinite(rssi)]
        quality_score = None
        if rssi.size:
            rssi_mean = float(np.mean(rssi))
            quality_score = float(max(0.0, min(100.0, (rssi_mean + 120.0) / 60.0 * 100.0)))

        health_status = None
        if quality_score is not None:
            if quality_score >= 80:
                health_status = "GOOD"
            elif quality_score >= 50:
                health_status = "FAIR"
            else:
                health_status = "POOR"

        rows.append(
            {
                "station_callsign": station,
                "packet_total": packet_total,
                "max_distance_km": max_distance_km,
                "p95_distance_km": p95_distance_km,
                "quality_score": quality_score,
                "horizon_efficiency": None,
                "health_status": health_status,
            }
        )

    if invalid_coords and len(rows) < 2:
        return {
            "implemented": False,
            "summary": {
                "reason": "invalid_station_coordinates",
                "configured_station_count": len(stations),
                "comparable_station_count": len(rows),
            },
            "data": None,
        }
    if len(rows) < 2:
        return {
            "implemented": False,
            "summary": {
                "reason": "no_packets_for_configured_stations",
                "configured_station_count": len(stations),
                "comparable_station_count": len(rows),
            },
            "data": None,
        }

    data = pd.DataFrame(rows)
    rank_score = (
        0.4 * _norm(data["p95_distance_km"])
        + 0.4 * _norm(data["quality_score"])
        + 0.2 * _norm(data["packet_total"])
    )
    data["rank_score"] = rank_score
    data = data.sort_values("rank_score", ascending=False)

    summary = {
        "station_count": int(len(data)),
        "best_station": data.iloc[0]["station_callsign"],
        "best_rank_score": float(data.iloc[0]["rank_score"]),
    }

    return {"implemented": True, "summary": summary, "data": data}
