from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class StationActivity:
    packet_count: Optional[int] = None
    unique_aircraft: Optional[int] = None


@dataclass(frozen=True)
class StationDirection:
    corridor_center_deg: Optional[float] = None
    dominant_corridor_share: Optional[float] = None
    coverage_uniformity_score: Optional[float] = None
    gap_count: Optional[int] = None
    largest_gap_deg: Optional[float] = None


@dataclass(frozen=True)
class StationNetwork:
    station_count: Optional[int] = None
    co_visible_stations: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class StationImpact:
    impact_score: Optional[float] = None
    only_seen_aircraft_count: Optional[int] = None


@dataclass(frozen=True)
class StationInsight:
    station_id: str
    health_status: str
    activity: StationActivity
    direction: StationDirection
    network: StationNetwork
    impact: StationImpact
