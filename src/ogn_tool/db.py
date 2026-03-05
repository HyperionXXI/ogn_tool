# src/ogn_tool/db.py
from __future__ import annotations

import sqlite3
from pathlib import Path


def connect(db_path: Path) -> sqlite3.Connection:
    # WAL DBs are fine; read-only dashboard can still read.
    # timeout avoids "database is locked" bursts when collector writes.
    conn = sqlite3.connect(str(db_path), timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn