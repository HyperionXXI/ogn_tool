from __future__ import annotations

import pandas as pd


def aircraft_redundancy(matrix: pd.DataFrame) -> pd.Series:
    if matrix is None or matrix.empty:
        return pd.Series(dtype=int)
    counts = matrix.groupby("src")["igate"].nunique()
    return counts.value_counts().sort_index()


def detect_network_blind_zones(df, grid_size_km=5):
    """
    Detect areas where RF reception is missing.
    Basic placeholder implementation.
    """
    if df is None or len(df) == 0:
        return pd.DataFrame()

    if "lat" not in df or "lon" not in df:
        return pd.DataFrame()

    grid = (
        df.groupby([
            (df["lat"] // (grid_size_km / 111)),
            (df["lon"] // (grid_size_km / 111)),
        ])
        .size()
        .reset_index(name="packet_count")
    )

    return grid



def build_reception_events(packets_df: pd.DataFrame) -> pd.DataFrame:
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


def compute_coverage_redundancy(reception_events: pd.DataFrame, station_reception: pd.DataFrame) -> pd.DataFrame:
    if reception_events is None or station_reception is None or reception_events.empty or station_reception.empty:
        return pd.DataFrame()
    df = station_reception.merge(
        reception_events[["event_key", "lat", "lon"]],
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



def enrich_coverage_grid(distance_df: pd.DataFrame, coverage_grid: pd.DataFrame) -> pd.DataFrame:
    if coverage_grid is None:
        return pd.DataFrame()
    if distance_df is None or distance_df.empty or "lat" not in distance_df.columns or "lon" not in distance_df.columns:
        return coverage_grid

    cell_size = float(coverage_grid["cell_size_deg"].iloc[0]) if not coverage_grid.empty and "cell_size_deg" in coverage_grid.columns else 0.01
    df_cells = distance_df.copy()
    df_cells["grid_lat"] = (pd.to_numeric(df_cells.get("lat"), errors="coerce") // cell_size) * cell_size
    df_cells["grid_lon"] = (pd.to_numeric(df_cells.get("lon"), errors="coerce") // cell_size) * cell_size
    agg = {
        "max_distance": ("distance_km", "max"),
    }
    if "altitude_m" in df_cells.columns:
        agg["mean_altitude"] = ("altitude_m", "mean")
    cell_stats = (
        df_cells.groupby(["grid_lat", "grid_lon"], dropna=False)
        .agg(**agg)
        .reset_index()
        .rename(columns={"grid_lat": "lat", "grid_lon": "lon"})
    )
    if coverage_grid.empty:
        return coverage_grid
    return coverage_grid.merge(cell_stats, on=["lat", "lon"], how="left")


def build_network_metrics(
    coverage_grid: pd.DataFrame,
    coverage_redundancy_grid: pd.DataFrame,
    blind_cells: pd.DataFrame,
    station_metrics: pd.DataFrame,
) -> dict:
    coverage_cells = int((coverage_grid["packets"] > 0).sum()) if coverage_grid is not None and not coverage_grid.empty and "packets" in coverage_grid.columns else 0
    redundancy_cells = int((coverage_redundancy_grid["station_count"] > 1).sum()) if coverage_redundancy_grid is not None and not coverage_redundancy_grid.empty and "station_count" in coverage_redundancy_grid.columns else 0
    blind_cells_count = int(len(blind_cells)) if blind_cells is not None else 0
    return {
        "station_count": int(len(station_metrics)) if station_metrics is not None and not station_metrics.empty else 0,
        "coverage_cells": coverage_cells,
        "redundancy_cells": redundancy_cells,
        "blind_cells": blind_cells_count,
        "network_resilience_score": (redundancy_cells / coverage_cells * 100.0) if coverage_cells else 0.0,
    }
