# src/ogn_tool/config.py
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except Exception:  # pragma: no cover
    load_dotenv = None


@dataclass(frozen=True)
class AppConfig:
    db_path: Path
    station_callsign: str = "FK50887"


def get_config() -> AppConfig:
    """
    Resolve config.

    Priority for DB:
    1) OGN_DB_PATH environment variable
    2) ./data/ogn_log.sqlite3
    """
    if load_dotenv:
        # Load local .env if present (non-fatal)
        load_dotenv()

    station_callsign = os.getenv("OGN_USER", "FK50887")
    db_env = os.getenv("OGN_DB_PATH")
    if db_env:
        return AppConfig(db_path=Path(db_env), station_callsign=station_callsign)

    return AppConfig(db_path=Path("data") / "ogn_log.sqlite3", station_callsign=station_callsign)
