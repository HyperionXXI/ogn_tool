from __future__ import annotations

from typing import Dict, List, Optional, Tuple

import pandas as pd

from ogn_tool.config import get_config as _get_config
from ogn_tool.data.db_repository import (
    db_meta as _db_meta,
    db_max_ts_epoch as _db_max_ts_epoch,
    optimize_db as _optimize_db,
    create_indexes as _create_indexes,
    rf_sanity_check as _rf_sanity_check,
    table_exists as _table_exists,
)
from ogn_tool.data.packets_repository import load_packets_window as _load_packets_window
from ogn_tool.data.receptions_repository import load_rf_receptions as _load_rf_receptions


def get_config():
    return _get_config()


def db_meta(db_path: str, query_log: Optional[List[Dict]] = None) -> Tuple[int, Optional[str]]:
    return _db_meta(db_path, query_log=query_log)


def db_max_ts_epoch(db_path: str) -> Optional[int]:
    return _db_max_ts_epoch(db_path)


def optimize_db(db_path: str, vacuum: bool = False) -> None:
    _optimize_db(db_path, vacuum=vacuum)


def create_indexes(db_path: str) -> None:
    _create_indexes(db_path)


def rf_sanity_check(db_path: str) -> List[str]:
    return _rf_sanity_check(db_path)


def load_packets_window(
    db_path: str,
    since_iso: str,
    since_epoch: int,
    dst_types: List[str],
    station_callsign: str,
    only_heard_by: bool,
    igate_filter: str,
    source_mode: str,
    qas_filter: str,
    limit_rows: int,
    query_log: Optional[List[Dict]] = None,
) -> pd.DataFrame:
    return _load_packets_window(
        db_path=db_path,
        since_iso=since_iso,
        since_epoch=since_epoch,
        dst_types=dst_types,
        station_callsign=station_callsign,
        only_heard_by=only_heard_by,
        igate_filter=igate_filter,
        source_mode=source_mode,
        qas_filter=qas_filter,
        limit_rows=limit_rows,
        query_log=query_log,
    )


def load_rf_receptions(
    db_path: str,
    since_epoch: int,
    limit_rows: int,
    station_id: Optional[str] = None,
    query_log: Optional[List[Dict]] = None,
) -> pd.DataFrame:
    return _load_rf_receptions(
        db_path=db_path,
        since_epoch=since_epoch,
        limit_rows=limit_rows,
        station_id=station_id,
        query_log=query_log,
    )


def table_exists(db_path: str, table_name: str) -> bool:
    if not table_name:
        return False
    import sqlite3
    con = sqlite3.connect(db_path, check_same_thread=False)
    try:
        return _table_exists(con, table_name)
    finally:
        con.close()
