from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class StationRFDiagnostics:
    """Legacy compatibility model retained for older reporting consumers."""

    station_id: str
    angular_entropy: float
    shadow_risk: float
    interpretation: str


@dataclass
class NetworkEngineeringReport:
    """Canonical typed report projection for the network analysis engine."""

    network_summary: dict[str, Any] = field(default_factory=dict)
    station_health_table: pd.DataFrame = field(default_factory=pd.DataFrame)
    network_redundancy: dict[str, Any] = field(default_factory=dict)
    network_confidence: dict[str, Any] = field(default_factory=dict)
    station_dependency: pd.DataFrame = field(default_factory=pd.DataFrame)
    station_dominance: pd.DataFrame = field(default_factory=pd.DataFrame)
    spatial_observations: pd.DataFrame = field(default_factory=pd.DataFrame)
    rf_signature: dict[str, Any] = field(default_factory=dict)
    recommended_actions: list[str] = field(default_factory=list)
    input_warnings: list[str] = field(default_factory=list)


from .network_engineering_report_builder import build_network_engineering_report

__all__ = [
    'StationRFDiagnostics',
    'NetworkEngineeringReport',
    'build_network_engineering_report',
]
