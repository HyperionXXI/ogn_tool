from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = [
    "aircraft_id",
    "timestamp",
    "lat",
    "lon",
    "altitude",
]


def _empty_states() -> pd.DataFrame:
    return pd.DataFrame(columns=REQUIRED_COLUMNS)


def extract_aircraft_states(df: pd.DataFrame) -> pd.DataFrame:
    """Extract unique aircraft states from normalized packet/reception rows.

    A state represents a unique aircraft position/time sample independent of
    RF reception multiplicity. Multiple receptions from different stations may
    reference the same aircraft state.

    Expected canonical inputs (normalized):
    - aircraft_id
    - timestamp
    - lat
    - lon
    - altitude (optional in source, retained as nullable)

    Compatibility aliases handled:
    - src -> aircraft_id
    - ts_epoch / ts_utc -> timestamp
    - altitude_m / alt -> altitude

    Returns:
        DataFrame with columns:
        - aircraft_id
        - timestamp
        - lat
        - lon
        - altitude
    """
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return _empty_states()

    work = df.copy()

    if "aircraft_id" not in work.columns:
        if "src" in work.columns:
            work["aircraft_id"] = work["src"]
        else:
            work["aircraft_id"] = pd.NA

    if "timestamp" not in work.columns:
        if "ts_epoch" in work.columns:
            work["timestamp"] = pd.to_numeric(work["ts_epoch"], errors="coerce")
        elif "ts_utc" in work.columns:
            dt = pd.to_datetime(work["ts_utc"], errors="coerce", utc=True)
            work["timestamp"] = (dt.view("int64") // 1_000_000_000)
        else:
            work["timestamp"] = pd.NA

    if "altitude" not in work.columns:
        if "altitude_m" in work.columns:
            work["altitude"] = work["altitude_m"]
        elif "alt" in work.columns:
            work["altitude"] = work["alt"]
        else:
            work["altitude"] = pd.NA

    if "lat" not in work.columns:
        work["lat"] = pd.NA
    if "lon" not in work.columns:
        work["lon"] = pd.NA

    states = pd.DataFrame(index=work.index)
    states["aircraft_id"] = work["aircraft_id"].astype("string")
    states["timestamp"] = pd.to_numeric(work["timestamp"], errors="coerce").astype("Int64")
    states["lat"] = pd.to_numeric(work["lat"], errors="coerce")
    states["lon"] = pd.to_numeric(work["lon"], errors="coerce")
    states["altitude"] = pd.to_numeric(work["altitude"], errors="coerce")

    # Keep only valid state-defining geometry/time rows.
    states = states.dropna(subset=["aircraft_id", "timestamp", "lat", "lon"])

    # Unique aircraft position/time states: receptions from multiple stations
    # collapse to one state row.
    states = states.drop_duplicates(subset=["aircraft_id", "timestamp", "lat", "lon"], keep="first")

    return states.reset_index(drop=True)


__all__ = [
    "extract_aircraft_states",
    "REQUIRED_COLUMNS",
]