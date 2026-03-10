from __future__ import annotations

import pandas as pd


def _bin_grid(df: pd.DataFrame, grid_size_km: float) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame(columns=["grid_lat", "grid_lon"])

    if grid_size_km <= 0:
        raise ValueError("grid_size_km must be positive")

    # Approximate degrees per km
    cell_size_deg = grid_size_km / 111.0

    out = df.copy()
    out["lat"] = pd.to_numeric(out.get("lat"), errors="coerce")
    out["lon"] = pd.to_numeric(out.get("lon"), errors="coerce")
    out = out.dropna(subset=["lat", "lon"])

    if out.empty:
        return pd.DataFrame(columns=["grid_lat", "grid_lon"])

    out["grid_lat"] = (out["lat"] // cell_size_deg) * cell_size_deg
    out["grid_lon"] = (out["lon"] // cell_size_deg) * cell_size_deg
    return out


def compute_network_density(df_packets: pd.DataFrame, grid_size_km: float) -> pd.DataFrame:
    """
    Compute network-wide packet density grid.

    Returns DataFrame with: grid_lat, grid_lon, network_packets
    """
    binned = _bin_grid(df_packets, grid_size_km)
    if binned.empty:
        return pd.DataFrame(columns=["grid_lat", "grid_lon", "network_packets"])

    grid = (
        binned.groupby(["grid_lat", "grid_lon"], dropna=False)
        .size()
        .reset_index(name="network_packets")
    )
    return grid


def compute_station_reception(
    df_packets: pd.DataFrame,
    station_id: str,
    grid_size_km: float,
) -> pd.DataFrame:
    """
    Compute station reception density grid for a single station.

    Returns DataFrame with: grid_lat, grid_lon, station_packets
    """
    if df_packets is None or df_packets.empty or not station_id:
        return pd.DataFrame(columns=["grid_lat", "grid_lon", "station_packets"])

    df_station = df_packets.copy()
    if "igate" in df_station.columns:
        df_station = df_station[df_station["igate"].astype(str) == str(station_id)]
    else:
        return pd.DataFrame(columns=["grid_lat", "grid_lon", "station_packets"])

    binned = _bin_grid(df_station, grid_size_km)
    if binned.empty:
        return pd.DataFrame(columns=["grid_lat", "grid_lon", "station_packets"])

    grid = (
        binned.groupby(["grid_lat", "grid_lon"], dropna=False)
        .size()
        .reset_index(name="station_packets")
    )
    return grid


def compute_coverage_probability(
    network_density: pd.DataFrame,
    station_reception: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compute coverage ratio as station_reception / network_density.

    Returns DataFrame with: grid_lat, grid_lon, network_packets,
    station_packets, coverage_ratio
    """
    if network_density is None or network_density.empty:
        return pd.DataFrame(
            columns=["grid_lat", "grid_lon", "network_packets", "station_packets", "coverage_ratio"]
        )

    merged = network_density.merge(
        station_reception,
        on=["grid_lat", "grid_lon"],
        how="left",
    )
    merged["station_packets"] = pd.to_numeric(merged.get("station_packets"), errors="coerce").fillna(0)
    merged["network_packets"] = pd.to_numeric(merged.get("network_packets"), errors="coerce").fillna(0)

    merged["coverage_ratio"] = merged["station_packets"] / merged["network_packets"].replace(0, pd.NA)
    merged["coverage_ratio"] = merged["coverage_ratio"].fillna(0)

    return merged[["grid_lat", "grid_lon", "network_packets", "station_packets", "coverage_ratio"]]
