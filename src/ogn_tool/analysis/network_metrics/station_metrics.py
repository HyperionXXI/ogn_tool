from __future__ import annotations

import pandas as pd


def station_aircraft_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return dataframe with columns:
    src (aircraft), igate (station), packets
    """
    if df is None or df.empty:
        return pd.DataFrame(columns=["src", "igate", "packets"])
    return (
        df.groupby(["src", "igate"])
        .size()
        .reset_index(name="packets")
    )


def station_overlap(matrix: pd.DataFrame) -> pd.DataFrame:
    if matrix is None or matrix.empty:
        return pd.DataFrame()
    pivot = matrix.pivot(index="src", columns="igate", values="packets").fillna(0)
    overlap = pivot.T.dot(pivot)
    return overlap


def station_metrics(df: pd.DataFrame, station: str) -> dict:
    if df is None or df.empty or station is None:
        return {"aircraft": 0, "packets": 0, "max_distance": None, "mean_distance": None}
    sub = df[df["igate"] == station]
    return {
        "aircraft": int(sub["src"].nunique()) if "src" in sub.columns else 0,
        "packets": int(len(sub)),
        "max_distance": float(sub["distance_km"].max()) if "distance_km" in sub.columns and not sub.empty else None,
        "mean_distance": float(sub["distance_km"].mean()) if "distance_km" in sub.columns and not sub.empty else None,
    }



def build_station_reception(packets_df: pd.DataFrame) -> pd.DataFrame:
    if packets_df is None or packets_df.empty or "src" not in packets_df.columns:
        return pd.DataFrame()
    df = packets_df.copy()
    if "ts_epoch" in df.columns:
        df["time_bucket"] = (pd.to_numeric(df["ts_epoch"], errors="coerce") // 2) * 2
    elif "ts_utc" in df.columns:
        ts = pd.to_datetime(df["ts_utc"], errors="coerce")
        df["time_bucket"] = (ts.astype("int64") // 1_000_000_000 // 2) * 2
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


def compute_station_overlap(station_reception: pd.DataFrame) -> pd.DataFrame:
    if station_reception is None or station_reception.empty:
        return pd.DataFrame()
    if "event_key" not in station_reception.columns or "station_id" not in station_reception.columns:
        return pd.DataFrame()
    incidence = pd.crosstab(station_reception["event_key"], station_reception["station_id"]) > 0
    overlap = incidence.T.dot(incidence)
    return overlap



def build_station_metrics(distance_df: pd.DataFrame, coverage_grid: pd.DataFrame) -> pd.DataFrame:
    if distance_df is None or distance_df.empty or "igate" not in distance_df.columns:
        return pd.DataFrame()

    df_station = distance_df.copy()
    cell_size = float(coverage_grid["cell_size_deg"].iloc[0]) if coverage_grid is not None and not coverage_grid.empty and "cell_size_deg" in coverage_grid.columns else 0.01
    df_station["grid_lat"] = (pd.to_numeric(df_station.get("lat"), errors="coerce") // cell_size) * cell_size
    df_station["grid_lon"] = (pd.to_numeric(df_station.get("lon"), errors="coerce") // cell_size) * cell_size
    station_metrics_df = (
        df_station.groupby("igate")
        .agg(
            packet_count=("igate", "size"),
            aircraft_count=("src", "nunique"),
            max_distance=("distance_km", "max"),
            p95_distance=("distance_km", lambda x: pd.Series(x).quantile(0.95)),
            coverage_cells=("grid_lat", "nunique"),
        )
        .reset_index()
    )
    src_igates = distance_df.groupby("src")["igate"].nunique()
    unique_src = src_igates[src_igates == 1].index
    shared_src = src_igates[src_igates > 1].index
    contrib = []
    for callsign in station_metrics_df["igate"].tolist():
        subset = df_station[df_station["igate"] == callsign]
        unique_packets = int(subset[subset["src"].isin(unique_src)].shape[0])
        shared_packets = int(subset[subset["src"].isin(shared_src)].shape[0])
        redundant_packets = shared_packets
        total_packets = int(subset.shape[0])
        contribution_score = (unique_packets / total_packets * 100.0) if total_packets else 0.0
        contrib.append(
            {
                "igate": callsign,
                "unique_packets": unique_packets,
                "shared_packets": shared_packets,
                "redundant_packets": redundant_packets,
                "contribution_score": contribution_score,
            }
        )
    contrib_df = pd.DataFrame(contrib)
    return station_metrics_df.merge(contrib_df, on="igate", how="left")
