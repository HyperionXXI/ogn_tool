from __future__ import annotations

from dataclasses import dataclass


@dataclass
class StationAdditionEvaluation:
    candidate_id: str
    lat: float
    lon: float
    aircraft_supported: int
    coverage_gain: int
    redundancy_gain: int
    priority_score: int
