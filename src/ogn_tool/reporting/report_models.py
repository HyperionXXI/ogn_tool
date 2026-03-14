from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NetworkEngineeringReport:
    network_status: str | None = None
    station_health: list[dict[str, Any]] = field(default_factory=list)
    critical_stations: list[dict[str, Any]] = field(default_factory=list)
    coverage_gaps: list[dict[str, Any]] = field(default_factory=list)
    recommended_new_stations: list[dict[str, Any]] = field(default_factory=list)
