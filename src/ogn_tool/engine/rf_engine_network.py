from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def build_radio_events(packets_df: pd.DataFrame) -> pd.DataFrame:
    if packets_df is None or packets_df.empty or "src" not in packets_df.columns:
        return pd.DataFrame()
    df = packets_df.copy()
    if "ts_epoch" in df.columns:
        df["time_bucket"] = (pd.to_numeric(df["ts_epoch"], errors="coerce") // 2) * 2
    elif "ts_utc" in df.columns:
        ts = pd.to_datetime(df["ts_utc"], errors="coerce")
        df["time_bucket"] = (ts.view("int64") // 1_000_000_000 // 2) * 2
    else:
        df["time_bucket"] = pd.NA
    df["lat_round"] = pd.to_numeric(df.get("lat"), errors="coerce").round(3)
    df["lon_round"] = pd.to_numeric(df.get("lon"), errors="coerce").round(3)
    df["event_key"] = (
        df["src"].astype(str)
        + "_"
        + df["time_bucket"].astype(str)
        + "_"
        + df["lat_round"].astype(str)
        + "_"
        + df["lon_round"].astype(str)
    )
    agg = {
        "timestamp": ("ts_epoch", "min") if "ts_epoch" in df.columns else ("time_bucket", "min"),
        "aircraft": ("src", "first"),
        "lat": ("lat", "mean"),
        "lon": ("lon", "mean"),
        "packet_count": ("src", "size"),
    }
    if "altitude_m" in df.columns:
        agg["altitude"] = ("altitude_m", "mean")
    if "igate" in df.columns:
        agg["station_count"] = ("igate", "nunique")
    events = df.groupby("event_key", dropna=False).agg(**agg).reset_index()
    if "altitude" not in events.columns:
        events["altitude"] = pd.NA
    if "station_count" not in events.columns:
        events["station_count"] = events["packet_count"]
    return events


def build_station_reception(packets_df: pd.DataFrame) -> pd.DataFrame:
    if packets_df is None or packets_df.empty or "src" not in packets_df.columns:
        return pd.DataFrame()
    df = packets_df.copy()
    if "ts_epoch" in df.columns:
        df["time_bucket"] = (pd.to_numeric(df["ts_epoch"], errors="coerce") // 2) * 2
    elif "ts_utc" in df.columns:
        ts = pd.to_datetime(df["ts_utc"], errors="coerce")
        df["time_bucket"] = (ts.view("int64") // 1_000_000_000 // 2) * 2
    else:
        df["time_bucket"] = pd.NA
    df["lat_round"] = pd.to_numeric(df.get("lat"), errors="coerce").round(3)
    df["lon_round"] = pd.to_numeric(df.get("lon"), errors="coerce").round(3)
    df["event_key"] = (
        df["src"].astype(str)
        + "_"
        + df["time_bucket"].astype(str)
        + "_"
        + df["lat_round"].astype(str)
        + "_"
        + df["lon_round"].astype(str)
    )
    cols = ["event_key"]
    if "igate" in df.columns:
        cols.append("igate")
    if "rssi_db" in df.columns:
        cols.append("rssi_db")
    elif "rssi" in df.columns:
        cols.append("rssi")
    if "snr_db" in df.columns:
        cols.append("snr_db")
    elif "snr" in df.columns:
        cols.append("snr")
    if "distance_km" in df.columns:
        cols.append("distance_km")
    return df[cols].rename(columns={"igate": "station_id"})


def compute_coverage_redundancy(radio_events: pd.DataFrame, station_reception: pd.DataFrame) -> pd.DataFrame:
    if radio_events is None or station_reception is None or radio_events.empty or station_reception.empty:
        return pd.DataFrame()
    df = station_reception.merge(
        radio_events[["event_key", "lat", "lon"]],
        on="event_key",
        how="left",
    )
    df["lat_cell"] = (pd.to_numeric(df["lat"], errors="coerce") / 0.05).round() * 0.05
    df["lon_cell"] = (pd.to_numeric(df["lon"], errors="coerce") / 0.05).round() * 0.05
    return (
        df.groupby(["lat_cell", "lon_cell"], dropna=False)
        .agg(
            station_count=("station_id", "nunique"),
            reception_count=("event_key", "count"),
        )
        .reset_index()
    )


def compute_blind_zones(coverage_redundancy: pd.DataFrame) -> pd.DataFrame:
    if coverage_redundancy is None or coverage_redundancy.empty or "station_count" not in coverage_redundancy.columns:
        return pd.DataFrame()
    return coverage_redundancy[coverage_redundancy["station_count"] <= 1].copy()


def compute_station_overlap(station_reception: pd.DataFrame) -> pd.DataFrame:
    if station_reception is None or station_reception.empty:
        return pd.DataFrame()
    if "event_key" not in station_reception.columns or "station_id" not in station_reception.columns:
        return pd.DataFrame()
    incidence = pd.crosstab(station_reception["event_key"], station_reception["station_id"]) > 0
    overlap = incidence.T.dot(incidence)
    return overlap


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
