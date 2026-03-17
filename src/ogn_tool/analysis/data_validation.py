from __future__ import annotations

from typing import Dict, Iterable, Tuple

import pandas as pd


def validate_coordinates(
    df: pd.DataFrame,
    lat_col: str = "lat",
    lon_col: str = "lon",
) -> pd.Series:
    if lat_col not in df.columns or lon_col not in df.columns:
        return pd.Series([True] * len(df), index=df.index)

    lat = pd.to_numeric(df[lat_col], errors="coerce")
    lon = pd.to_numeric(df[lon_col], errors="coerce")

    return lat.between(-90, 90) & lon.between(-180, 180)


def validate_distance(
    df: pd.DataFrame,
    distance_col: str = "distance_km",
) -> pd.Series:
    if distance_col not in df.columns:
        return pd.Series([True] * len(df), index=df.index)

    dist = pd.to_numeric(df[distance_col], errors="coerce")

    return dist > 0


def validate_snr(
    df: pd.DataFrame,
    snr_col: str = "snr",
) -> pd.Series:
    if snr_col not in df.columns:
        return pd.Series([True] * len(df), index=df.index)

    snr = pd.to_numeric(df[snr_col], errors="coerce")

    return snr.notna()


def validate_timestamp(
    df: pd.DataFrame,
    ts_col: str = "ts_epoch",
) -> pd.Series:
    if ts_col not in df.columns:
        return pd.Series([True] * len(df), index=df.index)

    ts = pd.to_numeric(df[ts_col], errors="coerce")

    return ts.notna() & (ts > 0)


def detect_duplicates(
    df: pd.DataFrame,
    subset: Iterable[str] | None = None,
) -> pd.Series:
    if df.empty:
        return pd.Series([], dtype=bool)

    if subset is None:
        candidates = [
            "ts_epoch",
            "lat",
            "lon",
            "aircraft",
            "igate",
            "receiver",
        ]
        subset = [col for col in candidates if col in df.columns]

    if not subset:
        return pd.Series([False] * len(df), index=df.index)

    return df.duplicated(subset=list(subset), keep="first")


def validate_dataset(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    if df is None or not isinstance(df, pd.DataFrame) or df.empty:
        return pd.DataFrame(), {
            "rows_total": 0,
            "rows_valid": 0,
            "invalid_coordinates": 0,
            "invalid_distance": 0,
            "invalid_snr": 0,
            "invalid_timestamp": 0,
            "duplicates": 0,
        }

    coord_ok = validate_coordinates(df)
    dist_ok = validate_distance(df)
    snr_ok = validate_snr(df)
    ts_ok = validate_timestamp(df)
    dup = detect_duplicates(df)

    valid_mask = coord_ok & dist_ok & snr_ok & ts_ok & ~dup

    report = {
        "rows_total": int(len(df)),
        "rows_valid": int(valid_mask.sum()),
        "invalid_coordinates": int((~coord_ok).sum()),
        "invalid_distance": int((~dist_ok).sum()),
        "invalid_snr": int((~snr_ok).sum()),
        "invalid_timestamp": int((~ts_ok).sum()),
        "duplicates": int(dup.sum()),
    }

    return df.loc[valid_mask].copy(), report
