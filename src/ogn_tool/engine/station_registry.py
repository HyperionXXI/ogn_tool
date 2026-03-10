from __future__ import annotations

from typing import Dict, Optional

from ogn_tool.domain.station import Station


class StationRegistry:
    """
    Registry maintaining known RF stations.
    """

    def __init__(self):
        self._stations: Dict[str, Station] = {}

    def get(self, station_id: str) -> Optional[Station]:
        return self._stations.get(station_id)

    def register(self, station: Station) -> None:
        self._stations[station.station_id] = station

    def all(self):
        return list(self._stations.values())
