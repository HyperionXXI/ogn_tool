from __future__ import annotations

import sqlite3
from typing import Dict, List, Optional

import pandas as pd


def load_rf_receptions(
    db_path: str,
    since_epoch: int,
    end_epoch: int | None,
    limit_rows: int,
    station_id: str | None = None,
    query_log: Optional[List[Dict]] = None,
) -> pd.DataFrame:
    q = ["SELECT * FROM packets WHERE ts_epoch >= ?"]
    params: List[object] = [int(since_epoch)]

    if end_epoch is not None:
        q.append("AND ts_epoch <= ?")
        params.append(int(end_epoch))

    if station_id:
        q.append("AND UPPER(COALESCE(igate, '')) = UPPER(?)")
        params.append(str(station_id))

    q.append("ORDER BY ts_epoch DESC")
    q.append("LIMIT ?")
    params.append(int(limit_rows))

    sql = " ".join(q)
    if query_log is not None:
        query_log.append({"sql": sql, "params": params})

    with sqlite3.connect(db_path, timeout=10) as con:
        return pd.read_sql_query(sql, con, params=params)
