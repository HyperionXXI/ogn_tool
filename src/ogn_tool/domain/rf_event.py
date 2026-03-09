from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class RFEvent:
    """Canonical radio reception event independent of protocol."""

    timestamp: float
    protocol: str
    emitter_id: str
    receiver_id: str

    lat: Optional[float] = None
    lon: Optional[float] = None
    alt: Optional[float] = None

    rssi: Optional[float] = None
    snr: Optional[float] = None

    metadata: Optional[Dict] = None
