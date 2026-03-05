# srcogn_toolconfig.py
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig
    db_path Path


def get_config() - AppConfig
    
    DB path resolution (standard)
    1) OGN_DB_PATH env var
    2) .dataogn_log.sqlite3 (fallback)
    
    env = os.getenv(OGN_DB_PATH, ).strip()
    if env
        return AppConfig(db_path=Path(env))

    fallback = Path(data)  ogn_log.sqlite3
    return AppConfig(db_path=fallback)