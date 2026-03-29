from __future__ import annotations

import sqlite3

import pandas as pd


def load_stations(db_path: str) -> pd.DataFrame:
    with sqlite3.connect(db_path, timeout=10) as con:
        return pd.read_sql_query(
            "SELECT DISTINCT igate FROM packets WHERE igate IS NOT NULL",
            con,
        )
