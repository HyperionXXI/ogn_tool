from __future__ import annotations

import math

from ogn_tool.domain.rf_event import RFEvent
from ogn_tool.domain.rf_observation import RFObservation
from ogn_tool.engine.station_registry import StationRegistry


class ObservationBuilder:
    """
    Responsible for transforming RFEvent objects into RFObservation objects.

    This class will progressively integrate spatial calculations,
    station registry lookups, and propagation metrics.
    """

    def __init__(self, station_registry: StationRegistry | None = None):
        self.station_registry = station_registry

    def build(self, event: RFEvent) -> RFObservation:
        """
        Convert a raw RFEvent into an RFObservation.

        For now, this performs a minimal transformation.
        Enrichment will be added later.
        """

        observation = RFObservation(event=event)

        if self.station_registry is not None:
            station = self.station_registry.get(event.receiver_id)
            if station is not None:
                observation.receiver_lat = station.lat
                observation.receiver_lon = station.lon
                observation.receiver_alt = station.alt

        if (
            observation.receiver_lat is not None
            and observation.receiver_lon is not None
            and event.lat is not None
            and event.lon is not None
        ):
            observation.distance_km = _distance_km(
                event.lat,
                event.lon,
                observation.receiver_lat,
                observation.receiver_lon,
            )
            observation.bearing_deg = _bearing_deg(
                event.lat,
                event.lon,
                observation.receiver_lat,
                observation.receiver_lon,
            )
        else:
            observation.distance_km = None
            observation.bearing_deg = None

        return observation


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )

    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    dlambda = math.radians(lon2 - lon1)

    x = math.sin(dlambda) * math.cos(phi2)
    y = (
        math.cos(phi1) * math.sin(phi2)
        - math.sin(phi1) * math.cos(phi2) * math.cos(dlambda)
    )

    bearing = math.degrees(math.atan2(x, y))

    return (bearing + 360) % 360
