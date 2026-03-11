from __future__ import annotations

from typing import Iterable, Dict, List

from ogn_tool.analysis.aprs_adapter import packet_row_to_rfevent
from ogn_tool.engine.observation_builder import ObservationBuilder
from ogn_tool.domain.rf_observation import RFObservation


builder = ObservationBuilder()


def build_observations(
    events: Iterable,
    builder: ObservationBuilder,
) -> List[RFObservation]:
    """
    Convert RFEvent objects into RFObservation objects.
    """
    observations: List[RFObservation] = []
    for event in events:
        obs = builder.build(event)
        observations.append(obs)
    return observations


def build_observations_from_packets(
    packet_rows: Iterable[Dict],
    builder: ObservationBuilder | None = None,
) -> List[RFObservation]:
    """
    Convert APRS packet rows directly into RFObservations.
    """
    if builder is None:
        builder = ObservationBuilder()

    events = []
    for row in packet_rows:
        event = packet_row_to_rfevent(row)
        events.append(event)

    return build_observations(events, builder)
