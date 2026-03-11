from __future__ import annotations

from typing import Any

import pandas as pd


CANONICAL_COLUMNS = [
    "station_id",
    "aircraft_id",
    "timestamp",
    "lat",
    "lon",
    "altitude",
    "snr",
    "freq_offset",
    "bit_errors",
]


def _first_existing(df: pd.DataFrame, candidates: list[str]) -> pd.Series:
    for col in candidates:
        if col in df.columns:
            return df[col]
    return pd.Series([pd.NA] * len(df), index=df.index, dtype="object")


def _to_timestamp(df: pd.DataFrame) -> pd.Series:
    if "ts_epoch" in df.columns:
        ts = pd.to_numeric(df["ts_epoch"], errors="coerce")
        return ts.astype("Int64")

    if "timestamp" in df.columns:
        ts = pd.to_numeric(df["timestamp"], errors="coerce")
        return ts.astype("Int64")

    if "ts_utc" in df.columns:
        dt = pd.to_datetime(df["ts_utc"], errors="coerce", utc=True)
        # Use nullable integer seconds since epoch.
        return (dt.view("int64") // 1_000_000_000).astype("Int64")

    return pd.Series([pd.NA] * len(df), index=df.index, dtype="Int64")


def normalize_rf_receptions(
    packets_df: pd.DataFrame,
    keep_legacy_aliases: bool = True,
) -> pd.DataFrame:
    """Normalize packet/reception rows into canonical RF receptions.

    Canonical schema target (docs/core/DATA_CONTRACT.md):
    - station_id
    - aircraft_id
    - timestamp
    - lat
    - lon
    - altitude
    - snr
    - freq_offset
    - bit_errors

    Args:
        packets_df: Raw packet/reception-like dataframe.
        keep_legacy_aliases: If True, append legacy compatibility aliases
            (`igate`, `src`, `ts_epoch`) for downstream code that still expects
            packet-oriented column names.

    Returns:
        DataFrame containing canonical columns plus optional compatibility
        aliases and passthrough metadata columns when available.
    """
    if packets_df is None or not isinstance(packets_df, pd.DataFrame) or packets_df.empty:
        cols = list(CANONICAL_COLUMNS)
        if keep_legacy_aliases:
            cols.extend(["igate", "src", "ts_epoch"])
        return pd.DataFrame(columns=cols)

    df = packets_df.copy()

    out = pd.DataFrame(index=df.index)
    out["station_id"] = _first_existing(df, ["station_id", "receiver", "igate"])
    out["aircraft_id"] = _first_existing(df, ["aircraft_id", "src", "aircraft", "emitter_id"])
    out["timestamp"] = _to_timestamp(df)

    out["lat"] = pd.to_numeric(_first_existing(df, ["lat"]), errors="coerce")
    out["lon"] = pd.to_numeric(_first_existing(df, ["lon"]), errors="coerce")

    out["altitude"] = pd.to_numeric(
        _first_existing(df, ["altitude", "altitude_m", "alt"]),
        errors="coerce",
    )

    out["snr"] = pd.to_numeric(_first_existing(df, ["snr", "snr_db"]), errors="coerce")
    out["freq_offset"] = pd.to_numeric(_first_existing(df, ["freq_offset"]), errors="coerce")
    out["bit_errors"] = pd.to_numeric(_first_existing(df, ["bit_errors"]), errors="coerce").astype("Int64")

    # Preserve commonly useful metadata when present.
    for col in ["packet_id", "id", "qas", "raw", "dst", "protocol"]:
        if col in df.columns:
            out[col] = df[col]

    if keep_legacy_aliases:
        out["igate"] = out["station_id"]
        out["src"] = out["aircraft_id"]
        out["ts_epoch"] = out["timestamp"]

    # Keep canonical columns first for predictable schema handling.
    canonical_plus = CANONICAL_COLUMNS + [
        c for c in out.columns if c not in CANONICAL_COLUMNS
    ]
    return out[canonical_plus]


def map_row_to_canonical(row: dict[str, Any]) -> dict[str, Any]:
    """Map a single packet/reception row dict to canonical RF fields."""
    frame = pd.DataFrame([row])
    normalized = normalize_rf_receptions(frame, keep_legacy_aliases=False)
    if normalized.empty:
        return {k: None for k in CANONICAL_COLUMNS}
    return normalized.iloc[0].to_dict()


__all__ = [
    "CANONICAL_COLUMNS",
    "normalize_rf_receptions",
    "map_row_to_canonical",
]