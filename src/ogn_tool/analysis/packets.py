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
