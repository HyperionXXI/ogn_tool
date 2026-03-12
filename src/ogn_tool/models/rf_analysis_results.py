from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class RFAnalysisResults:
    feature_matrix: Optional[Any] = None
    coverage: Optional[Any] = None
    visibility: Optional[Any] = None
    blind_zones: Optional[Any] = None
    antenna_pattern: Optional[Any] = None
    antenna_shadow_sectors: Optional[list] = None
    network_graph: Optional[Any] = None
    network_metrics: Optional[Any] = None
    network_timeseries: Optional[Any] = None
    network_events: Optional[Any] = None
    network_evolution: Optional[Any] = None
    station_suggestions: Optional[Any] = None
    metrics: Optional[dict] = None
