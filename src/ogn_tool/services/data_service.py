from __future__ import annotations

from typing import List, Optional, Dict
from datetime import datetime, timedelta, timezone

import pandas as pd

from ogn_tool.config import get_config
from ogn_tool.data.db_repository import (
    db_meta,
    db_max_ts_epoch,
    optimize_db,
    create_indexes,
    rf_sanity_check,
    table_exists_db,
)
from ogn_tool.data.packets_repository import load_packets_window
from ogn_tool.data.receptions_repository import load_rf_receptions


__all__ = [
    "get_config",
    "db_meta",
    "db_max_ts_epoch",
    "optimize_db",
    "create_indexes",
    "rf_sanity_check",
    "load_packets_window",
    "load_packets",
    "load_rf_receptions",
    "table_exists",
]


def table_exists(db_path: str, table_name: str) -> bool:
    return table_exists_db(db_path, table_name)


def load_packets():
    """
    Load a default packets window for UI pages without explicit filters.
    """
    cfg = get_config()
    now = datetime.now(timezone.utc)
    since_dt = now - timedelta(hours=6)
    return load_packets_window(
        db_path=str(cfg.db_path),
        since_iso=since_dt.isoformat().replace("+00:00", "+00:00"),
        since_epoch=int(since_dt.timestamp()),
        dst_types=["OGNFNT", "OGFLR", "OGFLR7", "OGNSDR", "OGNDVS"],
        station_callsign=cfg.station_callsign,
        only_heard_by=True,
        igate_filter="",
        source_mode="Heard-by station",
        qas_filter="",
        limit_rows=25000,
        query_log=None,
    )
