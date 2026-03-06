"""
Coverage grid loader.
"""

from __future__ import annotations

import os
import sqlite3
from typing import Optional

import pandas as pd


def load_coverage_grid(db_path: str) -> Optional[pd.DataFrame]:
    if not db_path or not os.path.exists(db_path):
        return None

    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='coverage_grid'"
        ).fetchone()
        if row is None:
            return None

        cols = {r[1] for r in con.execute("PRAGMA table_info(coverage_grid)")}
        required = {
            "cell_x",
            "cell_y",
            "lat",
            "lon",
            "max_distance_km",
            "best_rssi_db",
            "packet_count",
            "last_ts_epoch",
        }
        if not cols or not required.issubset(cols):
            return None

        sql = """
        SELECT
            cell_x,
            cell_y,
            lat,
            lon,
            max_distance_km,
            best_rssi_db,
            packet_count,
            last_ts_epoch
        FROM coverage_grid
        """
        return pd.read_sql_query(sql, con)
    except sqlite3.OperationalError:
        return None
    finally:
        con.close()
