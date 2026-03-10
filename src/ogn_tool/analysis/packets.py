from __future__ import annotations

import pandas as pd


def station_packets_query() -> str:
    return """
    SELECT
        lat,
        lon,
        ts_epoch,
        src AS aircraft
    FROM packets
    WHERE igate = :station
    AND lat IS NOT NULL
    AND lon IS NOT NULL
    """


def deduplicate_packets(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate packet rows to stabilize downstream analysis."""
    if df is None or df.empty:
        return df if df is not None else pd.DataFrame()
    # Default deduplication based on all columns (may be refined later)
    return df.drop_duplicates()
