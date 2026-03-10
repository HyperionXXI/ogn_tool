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
    Remove duplicate packets based on src + timestamp.
    """
    if df is None or len(df) == 0:
        return df

    return df.drop_duplicates(subset=["src", "ts_utc"])
