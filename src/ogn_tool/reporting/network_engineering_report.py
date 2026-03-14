from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class StationRFDiagnostics:
    station_id: str
    angular_entropy: float
    shadow_risk: float
    interpretation: str


@dataclass
class NetworkEngineeringReport:
    station_diagnostics: Dict[str, StationRFDiagnostics] = field(default_factory=dict)
    network_summary: Dict[str, Any] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)


from .report_builder import build_network_engineering_report

__all__ = ["StationRFDiagnostics", "NetworkEngineeringReport", "build_network_engineering_report"]
