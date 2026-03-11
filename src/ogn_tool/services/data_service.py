from __future__ import annotations

from typing import List, Optional, Dict

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
    "load_rf_receptions",
    "table_exists",
]


def table_exists(db_path: str, table_name: str) -> bool:
    return table_exists_db(db_path, table_name)
