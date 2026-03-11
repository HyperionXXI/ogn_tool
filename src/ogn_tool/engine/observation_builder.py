from __future__ import annotations

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

        observation = RFObservation(
            event=event
        )

        return observation
