from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple


def _connect(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(db_path, timeout=10)
    con.row_factory = sqlite3.Row
    return con




def ensure_packets_schema(db_path: str) -> None:
    with _connect(db_path) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS packets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts_utc TEXT NOT NULL,
                ts_epoch INTEGER,
                ts_ns INTEGER,
                src TEXT,
                dst TEXT,
                igate TEXT,
                qas TEXT,
                lat REAL,
                lon REAL,
                raw TEXT
            )
            """
        )
        cols = {row[1] for row in con.execute("PRAGMA table_info(packets)")}
        if "ts_epoch" not in cols:
            con.execute("ALTER TABLE packets ADD COLUMN ts_epoch INTEGER")
        if "ts_ns" not in cols:
            con.execute("ALTER TABLE packets ADD COLUMN ts_ns INTEGER")

def table_exists_db(db_path: str, table_name: str) -> bool:
    with _connect(db_path) as con:
        row = con.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
    return row is not None


def db_max_ts_epoch(db_path: str) -> Optional[int]:
    ensure_packets_schema(db_path)
    if not table_exists_db(db_path, "packets"):
        return None
    with _connect(db_path) as con:
        row = con.execute("SELECT MAX(ts_epoch) AS mx FROM packets").fetchone()
    if row is None:
        return None
    value = row["mx"]
    return int(value) if value is not None else None


def db_meta(db_path: str, query_log: Optional[List[Dict]] = None) -> Tuple[int, Optional[str]]:
    ensure_packets_schema(db_path)
    if not table_exists_db(db_path, "packets"):
        return 0, None
    with _connect(db_path) as con:
        row = con.execute("SELECT COUNT(*) AS n, MAX(ts_epoch) AS mx FROM packets").fetchone()
    count = int(row["n"]) if row and row["n"] is not None else 0
    mx = row["mx"] if row else None
    ts_utc = None
    if mx is not None:
        ts_utc = datetime.fromtimestamp(int(mx), tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S UTC")
    return count, ts_utc


def optimize_db(db_path: str, vacuum: bool = False) -> None:
    with _connect(db_path) as con:
        con.execute("PRAGMA optimize")
        if vacuum:
            con.execute("VACUUM")


def create_indexes(db_path: str) -> None:
    ensure_packets_schema(db_path)
    if not table_exists_db(db_path, "packets"):
        return
    with _connect(db_path) as con:
        con.execute("CREATE INDEX IF NOT EXISTS idx_packets_ts_epoch ON packets(ts_epoch)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_packets_ts_ns ON packets(ts_ns)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_packets_igate ON packets(igate)")


def rf_sanity_check(db_path: str) -> List[str]:
    ensure_packets_schema(db_path)
    checks: List[str] = []
    if not table_exists_db(db_path, "packets"):
        checks.append("missing table: packets")
        return checks
    with _connect(db_path) as con:
        row = con.execute("PRAGMA table_info(packets)").fetchall()
    cols = {r[1] for r in row}
    required = {"ts_epoch", "ts_ns", "src", "igate", "lat", "lon"}
    missing = sorted(required - cols)
    if missing:
        checks.append(f"missing columns: {', '.join(missing)}")
    return checks
