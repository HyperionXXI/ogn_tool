from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class Station:
    """
    Represents a ground receiver station in the RF network.
    """

    station_id: str

    lat: Optional[float] = None
    lon: Optional[float] = None
    alt: Optional[float] = None

    name: Optional[str] = None
    metadata: Optional[dict] = None
