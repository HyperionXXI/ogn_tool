from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional

from .rf_event import RFEvent


@dataclass
class RFObservation:
    """
    Enriched analytical representation of a radio reception.

    RFObservation is derived from an RFEvent and augmented with
    spatial relationships between emitter and receiver.

    This object is protocol-agnostic and intended to feed RF
    propagation and network analysis engines.
    """

    event: RFEvent

    receiver_lat: Optional[float] = None
    receiver_lon: Optional[float] = None
    receiver_alt: Optional[float] = None

    distance_km: Optional[float] = None
    bearing_deg: Optional[float] = None
    relative_alt_m: Optional[float] = None

    redundancy_count: Optional[int] = None

    metadata: Optional[Dict] = None
