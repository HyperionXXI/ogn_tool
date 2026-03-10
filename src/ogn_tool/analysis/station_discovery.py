from __future__ import annotations

from typing import Iterable, Dict

from ogn_tool.domain.station import Station
from ogn_tool.engine.station_registry import StationRegistry


def register_stations_from_packets(
    rows: Iterable[Dict],
    registry: StationRegistry,
):
    """
    Discover stations from packet rows and register them.

    Packets contain the igate identifier which represents
    the receiving ground station.
    """

    for row in rows:
        station_id = row.get("igate")

        if station_id is None:
            continue

        if registry.get(station_id) is None:
            registry.register(Station(station_id=station_id))
