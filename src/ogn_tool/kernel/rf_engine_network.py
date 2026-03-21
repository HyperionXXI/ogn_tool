from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from ogn_tool.kernel.network_metrics_kernel import (
    build_radio_events,
    build_station_reception,
    compute_blind_zones,
    compute_coverage_redundancy,
    compute_station_overlap,
)


def inspect_zone_impl(engine: Any, lat: float, lon: float, radius_km: float = 5.0) -> dict:
    if lat is None or lon is None:
        return {
            "events_count": 0,
            "stations": [],
            "redundancy_mean": 0.0,
            "max_distance_km": None,
        }

    dataset = engine._last_dataset or engine.build_analysis_dataset(
        dataset_mode=engine._last_dataset_mode or "STRICT_RF",
        station_id=engine._last_station_id,
    )
    radio_events = dataset.get("radio_events") or pd.DataFrame()
    station_reception = dataset.get("station_reception") or pd.DataFrame()

    if radio_events.empty or "lat" not in radio_events.columns or "lon" not in radio_events.columns:
        return {
            "events_count": 0,
            "stations": [],
            "redundancy_mean": 0.0,
            "max_distance_km": None,
        }

    lat_r = np.radians(pd.to_numeric(radio_events["lat"], errors="coerce"))
    lon_r = np.radians(pd.to_numeric(radio_events["lon"], errors="coerce"))
    lat0 = np.radians(float(lat))
    lon0 = np.radians(float(lon))
    dlat = lat_r - lat0
    dlon = lon_r - lon0
    a = np.sin(dlat / 2) ** 2 + np.cos(lat0) * np.cos(lat_r) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    dist_km = 6371.0 * c
    mask = dist_km <= float(radius_km)
    events_zone = radio_events[mask]

    if events_zone.empty:
        return {
            "events_count": 0,
            "stations": [],
            "redundancy_mean": 0.0,
            "max_distance_km": None,
        }

    stations = []
    max_distance = None
    if not station_reception.empty and "event_key" in station_reception.columns:
        subset = station_reception[station_reception["event_key"].isin(events_zone["event_key"])]
        if "station_id" in subset.columns:
            stations = sorted(subset["station_id"].astype(str).dropna().unique().tolist())
        if "distance_km" in subset.columns:
            max_distance = pd.to_numeric(subset["distance_km"], errors="coerce").max()

    redundancy_mean = (
        pd.to_numeric(events_zone.get("station_count"), errors="coerce").mean()
        if "station_count" in events_zone.columns
        else 0.0
    )

    return {
        "events_count": int(len(events_zone)),
        "stations": stations,
        "redundancy_mean": float(redundancy_mean) if pd.notna(redundancy_mean) else 0.0,
        "max_distance_km": max_distance,
    }


__all__ = [
    "build_radio_events",
    "build_station_reception",
    "compute_coverage_redundancy",
    "compute_blind_zones",
    "compute_station_overlap",
    "inspect_zone_impl",
]
