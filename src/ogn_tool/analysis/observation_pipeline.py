from __future__ import annotations

from typing import Iterable, Dict, List

from ogn_tool.analysis.aprs_adapter import packet_row_to_rfevent
from ogn_tool.domain.rf_event import RFEvent
from ogn_tool.engine.observation_builder import ObservationBuilder
from ogn_tool.domain.rf_observation import RFObservation


builder = ObservationBuilder()


def packets_to_observations(rows: Iterable[Dict]) -> List[RFObservation]:
    """
    Convert database packet rows into RFObservation objects.
    """

    observations: List[RFObservation] = []

    for row in rows:
        event = packet_row_to_rfevent(row)
        observation = builder.build(event)
        observations.append(observation)

    return observations


def build_observations(
    events: Iterable[RFEvent],
    builder: ObservationBuilder,
) -> List[RFObservation]:
    observations: List[RFObservation] = []

    for event in events:
        obs = builder.build(event)
        observations.append(obs)

    return observations


from ogn_tool.analysis.aprs_adapter import packet_row_to_rfevent


def build_observations_from_packets(
    packet_rows,
    builder,
):
    """
    Convert APRS packet rows directly into RFObservations.
    """

    events = []

    for row in packet_rows:
        event = packet_row_to_rfevent(row)
        events.append(event)

    return build_observations(events, builder)
