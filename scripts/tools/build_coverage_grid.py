#!/usr/bin/env python3
"""Build a coverage grid table from packets.

Creates (or updates) a coverage_grid table with spatial binning (1 km by default)
to speed up map rendering and analysis.
"""

from __future__ import annotations

import argparse
import datetime as dt
import math
import re
import sqlite3
import time
from typing import Iterable, List, Tuple


RE_DB = re.compile(r"(?P<db>\d+(?:\.\d+)?)\s*dB\b")


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    lat1r = math.radians(lat1)
    lon1r = math.radians(lon1)
    lat2r = math.radians(lat2)
    lon2r = math.radians(lon2)
    dlat = lat2r - lat1r
    dlon = lon2r - lon1r
    a = math.sin(dlat / 2.0) ** 2 + math.cos(lat1r) * math.cos(lat2r) * math.sin(dlon / 2.0) ** 2
    c = 2.0 * math.asin(math.sqrt(a))
    return r * c


def mercator_xy(lat: float, lon: float) -> Tuple[float, float]:
    r = 6378137.0
    x = r * math.radians(lon)
    y = r * math.log(math.tan(math.pi / 4.0 + math.radians(lat) / 2.0))
    return x, y


def inv_mercator(x: float, y: float) -> Tuple[float, float]:
    r = 6378137.0
    lon = math.degrees(x / r)
    lat = math.degrees(2.0 * math.atan(math.exp(y / r)) - math.pi / 2.0)
    return lat, lon


def parse_db_from_raw(raw: str) -> float | None:
    if not isinstance(raw, str):
        return None
    m = RE_DB.search(raw)
    if not m:
        return None
    try:
        return float(m.group("db"))
    except Exception:
        return None


def ensure_schema(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS coverage_grid (
            cell_x          INTEGER NOT NULL,
            cell_y          INTEGER NOT NULL,
            lat             REAL,
            lon             REAL,
            max_distance_km REAL,
            best_rssi_db    REAL,
            packet_count    INTEGER,
            last_ts_epoch   INTEGER,
            PRIMARY KEY (cell_x, cell_y)
        )
        """
    )
    con.execute("CREATE INDEX IF NOT EXISTS idx_covgrid_ts ON coverage_grid(last_ts_epoch DESC);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_covgrid_xy ON coverage_grid(cell_x, cell_y);")
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS coverage_grid_meta (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )


def get_meta_int(con: sqlite3.Connection, key: str, default: int) -> int:
    row = con.execute("SELECT value FROM coverage_grid_meta WHERE key=?", (key,)).fetchone()
    if not row:
        return default
    try:
        return int(row[0])
    except Exception:
        return default


def set_meta_int(con: sqlite3.Connection, key: str, value: int) -> None:
    con.execute(
        """
        INSERT INTO coverage_grid_meta (key, value)
        VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value
        """,
        (key, str(int(value))),
    )


def fetch_packets(con: sqlite3.Connection, since_epoch: int, batch: int) -> Iterable[List[Tuple]]:
    last_id = 0
    while True:
        rows = con.execute(
            """
            SELECT id, ts_epoch, lat, lon, raw
            FROM packets
            WHERE id > ?
              AND ts_epoch IS NOT NULL
              AND ts_epoch >= ?
              AND lat IS NOT NULL
              AND lon IS NOT NULL
            ORDER BY id
            LIMIT ?
            """,
            (last_id, int(since_epoch), int(batch)),
        ).fetchall()
        if not rows:
            break
        last_id = rows[-1][0]
        yield rows


def main() -> int:
    ap = argparse.ArgumentParser(description="Build coverage grid from packets.")
    ap.add_argument("--db", required=True, help="Path to SQLite DB")
    ap.add_argument("--cell-km", type=float, default=1.0, help="Grid cell size in km (default: 1.0)")
    ap.add_argument("--since-hours", type=int, default=24, help="Lookback window in hours (default: 24)")
    ap.add_argument("--incremental", action="store_true", help="Only process packets newer than last grid update")
    ap.add_argument("--batch", type=int, default=50000, help="Batch size (rows)")
    ap.add_argument("--station-lat", type=float, default=None, help="Station latitude")
    ap.add_argument("--station-lon", type=float, default=None, help="Station longitude")
    args = ap.parse_args()

    if args.station_lat is None or args.station_lon is None:
        raise SystemExit("Station lat/lon required. Pass --station-lat and --station-lon.")
    station_lat = float(args.station_lat)
    station_lon = float(args.station_lon)

    cell_m = float(args.cell_km) * 1000.0

    con = sqlite3.connect(args.db, timeout=30)
    try:
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
        ensure_schema(con)

        if args.incremental:
            since_epoch = get_meta_int(con, "last_ts_epoch", 0)
        else:
            since_epoch = int((dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=args.since_hours)).timestamp())

        total = 0
        t0 = time.time()
        max_ts_seen = since_epoch

        for rows in fetch_packets(con, since_epoch, args.batch):
            updates = {}
            for _, ts_epoch, lat, lon, raw in rows:
                if ts_epoch and ts_epoch > max_ts_seen:
                    max_ts_seen = ts_epoch
                x, y = mercator_xy(float(lat), float(lon))
                cell_x = int(math.floor(x / cell_m))
                cell_y = int(math.floor(y / cell_m))

                cx = (cell_x + 0.5) * cell_m
                cy = (cell_y + 0.5) * cell_m
                clat, clon = inv_mercator(cx, cy)
                dist = haversine_km(station_lat, station_lon, clat, clon)
                rssi = parse_db_from_raw(raw)

                key = (cell_x, cell_y)
                entry = updates.get(key)
                if entry is None:
                    updates[key] = {
                        "cell_x": cell_x,
                        "cell_y": cell_y,
                        "lat": clat,
                        "lon": clon,
                        "max_distance_km": dist,
                        "best_rssi_db": rssi,
                        "packet_count": 1,
                        "last_ts_epoch": ts_epoch,
                    }
                else:
                    entry["packet_count"] += 1
                    entry["last_ts_epoch"] = max(entry["last_ts_epoch"], ts_epoch)
                    if dist > entry["max_distance_km"]:
                        entry["max_distance_km"] = dist
                    if rssi is not None and (entry["best_rssi_db"] is None or rssi > entry["best_rssi_db"]):
                        entry["best_rssi_db"] = rssi

            if updates:
                con.executemany(
                    """
                    INSERT INTO coverage_grid (cell_x, cell_y, lat, lon, max_distance_km, best_rssi_db, packet_count, last_ts_epoch)
                    VALUES (:cell_x, :cell_y, :lat, :lon, :max_distance_km, :best_rssi_db, :packet_count, :last_ts_epoch)
                    ON CONFLICT(cell_x, cell_y) DO UPDATE SET
                        lat=excluded.lat,
                        lon=excluded.lon,
                        max_distance_km=MAX(coverage_grid.max_distance_km, excluded.max_distance_km),
                        best_rssi_db=MAX(coverage_grid.best_rssi_db, excluded.best_rssi_db),
                        packet_count=coverage_grid.packet_count + excluded.packet_count,
                        last_ts_epoch=MAX(coverage_grid.last_ts_epoch, excluded.last_ts_epoch)
                    """,
                    list(updates.values()),
                )
                con.commit()
                total += sum(v["packet_count"] for v in updates.values())
                rate = int(total / max(time.time() - t0, 1))
                print(f"Processed ~{total} packets (rate ~{rate}/s)")

        if args.incremental:
            set_meta_int(con, "last_ts_epoch", max_ts_seen)
            con.commit()

        print("Coverage grid build complete.")
        return 0
    finally:
        con.close()


if __name__ == "__main__":
    raise SystemExit(main())
