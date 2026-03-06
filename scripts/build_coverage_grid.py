#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build coverage_grid table from packets.
"""

from __future__ import annotations

import argparse
import math
import os
import re
import sqlite3
from typing import Iterable, Optional

import numpy as np
import pandas as pd


RSSI_RE = re.compile(r"([+-]?\d+(?:\.\d+)?)\s*dB")


def haversine_km(lat1: float, lon1: float, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
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


def iter_packets(
    con: sqlite3.Connection,
    since_epoch: Optional[int],
    chunksize: int = 200_000,
) -> Iterable[pd.DataFrame]:
    sql = """
    SELECT lat, lon, raw, ts_epoch
    FROM packets
    WHERE lat IS NOT NULL AND lon IS NOT NULL
    """
    params = []
    if since_epoch is not None:
        sql += " AND ts_epoch >= ?"
        params.append(int(since_epoch))
    return pd.read_sql_query(sql, con, params=params, chunksize=chunksize)


def build_grid(
    con: sqlite3.Connection,
    station_lat: float,
    station_lon: float,
    cell_size_deg: float,
    since_epoch: Optional[int],
) -> tuple[pd.DataFrame, int, int]:
    aggregates = []
    packets_read = 0
    packets_valid = 0

    for chunk in iter_packets(con, since_epoch=since_epoch):
        if chunk.empty:
            continue

        packets_read += int(len(chunk))
        lat = pd.to_numeric(chunk["lat"], errors="coerce")
        lon = pd.to_numeric(chunk["lon"], errors="coerce")
        ts_epoch = pd.to_numeric(chunk["ts_epoch"], errors="coerce")
        raw = chunk["raw"].astype(str)

        rssi = pd.to_numeric(raw.str.extract(RSSI_RE, expand=False), errors="coerce")

        mask = lat.notna() & lon.notna() & ts_epoch.notna()
        if not mask.any():
            continue

        lat = lat[mask]
        lon = lon[mask]
        ts_epoch = ts_epoch[mask]
        rssi = rssi[mask]
        packets_valid += int(len(lat))

        dist = haversine_km(station_lat, station_lon, lat.to_numpy(), lon.to_numpy())

        cell_x = np.floor(lon.to_numpy() / cell_size_deg).astype(int)
        cell_y = np.floor(lat.to_numpy() / cell_size_deg).astype(int)

        df = pd.DataFrame(
            {
                "cell_x": cell_x,
                "cell_y": cell_y,
                "lat": lat.to_numpy(),
                "lon": lon.to_numpy(),
                "distance_km": dist,
                "rssi_db": rssi.to_numpy(),
                "ts_epoch": ts_epoch.to_numpy(),
            }
        )

        agg = (
            df.groupby(["cell_x", "cell_y"], as_index=False)
            .agg(
                lat=("lat", "mean"),
                lon=("lon", "mean"),
                max_distance_km=("distance_km", "max"),
                best_rssi_db=("rssi_db", "max"),
                packet_count=("distance_km", "size"),
                last_ts_epoch=("ts_epoch", "max"),
            )
        )
        aggregates.append(agg)

    if not aggregates:
        return (
            pd.DataFrame(
                columns=[
                    "cell_x",
                    "cell_y",
                    "lat",
                    "lon",
                    "max_distance_km",
                    "best_rssi_db",
                    "packet_count",
                    "last_ts_epoch",
                ]
            ),
            packets_read,
            packets_valid,
        )

    all_agg = pd.concat(aggregates, ignore_index=True)
    final = (
        all_agg.groupby(["cell_x", "cell_y"], as_index=False)
        .agg(
            lat=("lat", "mean"),
            lon=("lon", "mean"),
            max_distance_km=("max_distance_km", "max"),
            best_rssi_db=("best_rssi_db", "max"),
            packet_count=("packet_count", "sum"),
            last_ts_epoch=("last_ts_epoch", "max"),
        )
    )
    return final, packets_read, packets_valid


def ensure_table(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS coverage_grid (
            cell_x INTEGER NOT NULL,
            cell_y INTEGER NOT NULL,
            lat REAL NOT NULL,
            lon REAL NOT NULL,
            max_distance_km REAL,
            best_rssi_db REAL,
            packet_count INTEGER NOT NULL,
            last_ts_epoch INTEGER NOT NULL
        )
        """
    )
    con.execute("DELETE FROM coverage_grid")
    con.execute("CREATE INDEX IF NOT EXISTS idx_covgrid_ts ON coverage_grid(last_ts_epoch DESC)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_covgrid_xy ON coverage_grid(cell_x, cell_y)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build coverage_grid from packets")
    parser.add_argument("--db", required=True, help="SQLite database path")
    parser.add_argument("--station-lat", type=float, required=True)
    parser.add_argument("--station-lon", type=float, required=True)
    parser.add_argument("--cell-size-deg", type=float, default=0.01)
    parser.add_argument("--since-epoch", type=int, default=None)
    args = parser.parse_args()

    if not os.path.exists(args.db):
        raise SystemExit(f"DB not found: {args.db}")

    con = sqlite3.connect(args.db)
    try:
        ensure_table(con)
        df_grid, packets_read, packets_valid = build_grid(
            con=con,
            station_lat=float(args.station_lat),
            station_lon=float(args.station_lon),
            cell_size_deg=float(args.cell_size_deg),
            since_epoch=args.since_epoch,
        )
        if not df_grid.empty:
            df_grid.to_sql("coverage_grid", con, if_exists="append", index=False)
        con.commit()
        print(f"packets read: {packets_read}")
        print(f"packets valid: {packets_valid}")
        print(f"coverage_grid rows: {len(df_grid)}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
