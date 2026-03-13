from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class NetworkEngineeringReport:
    network_status: str
    critical_stations: list[str] = field(default_factory=list)
    warning_stations: list[str] = field(default_factory=list)
    top_spof_stations: list[dict[str, Any]] = field(default_factory=list)
    top_gap_candidates: list[dict[str, Any]] = field(default_factory=list)
    top_redundancy_priorities: list[dict[str, Any]] = field(default_factory=list)
    top_station_addition_candidates: list[dict[str, Any]] = field(default_factory=list)
    summary_notes: list[str] = field(default_factory=list)
