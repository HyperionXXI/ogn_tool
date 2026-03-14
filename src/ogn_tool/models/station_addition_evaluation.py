from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StationAdditionEvaluation:
    lat: float
    lon: float
    aircraft_supported: int
    coverage_gain: int
    redundancy_gain: int
    priority_score: int
