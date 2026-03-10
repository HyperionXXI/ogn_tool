from __future__ import annotations

from typing import Dict

from ogn_tool.domain.rf_event import RFEvent


def packet_row_to_rfevent(row: Dict) -> RFEvent:
    """
    Convert a SQLite packet row into an RFEvent.

    Expected keys in row:
    - lat
    - lon
    - ts_epoch
    - aircraft
    - igate
    """

    return RFEvent(
        timestamp=row["ts_epoch"],
        protocol="APRS",
        emitter_id=row.get("aircraft") or row.get("src"),
        receiver_id=row["igate"],
        lat=row.get("lat"),
        lon=row.get("lon"),
        metadata={
            "_row_id": row.get("_row_id")
        },
    )
