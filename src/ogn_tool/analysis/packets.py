from __future__ import annotations


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


def deduplicate_packets(df):
    """
    Remove duplicate packets based on source and timestamp.
    """
    if df is None or len(df) == 0:
        return df

    src_col = "src" if "src" in df.columns else ("aircraft" if "aircraft" in df.columns else None)
    if src_col is None:
        return df

    if "ts_utc" in df.columns:
        ts_col = "ts_utc"
    elif "ts_epoch" in df.columns:
        ts_col = "ts_epoch"
    elif "timestamp" in df.columns:
        ts_col = "timestamp"
    else:
        return df

    return df.drop_duplicates(subset=[src_col, ts_col])
