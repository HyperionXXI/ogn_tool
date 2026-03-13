from dataclasses import dataclass
from typing import Any, Optional

from .network_graph_model import NetworkGraph


@dataclass
class RFAnalysisResults:
    """Canonical kernel output contract.

    Field classification for Phase 1 stabilization:
    - feature_matrix: intermediate pipeline/debug artifact
    - coverage/visibility/blind_zones/antenna_*: stable RF result surface
    - network_*: stable or evolving network result surface
    - station_suggestions: intelligence result surface
    - metrics: summary/compatibility container only
    """

    FIELD_CLASSIFICATION = {
        "feature_matrix": "intermediate",
        "coverage": "rf",
        "visibility": "rf",
        "blind_zones": "rf",
        "antenna_pattern": "rf",
        "antenna_shadow_sectors": "rf",
        "network_graph": "network",
        "network_metrics": "network",
        "network_timeseries": "network",
        "network_events": "network",
        "network_evolution": "network",
        "station_suggestions": "intelligence",
        "metrics": "summary",
    }

    FORBIDDEN_METRICS_KEYS = {
        "feature_matrix",
        "network_graph",
        "coverage",
        "antenna_pattern",
        "blind_zones",
        "blind_zone_grid",
        "distance_df",
        "grid_base",
    }

    # Intermediate pipeline/debug artifact. Not part of the stable public RF result contract.
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
    # Summary/compatibility container only. Must not become a second results object.
    metrics: Optional[dict] = None

    def validate(self) -> None:
        if self.metrics is not None:
            if not isinstance(self.metrics, dict):
                raise RuntimeError("RFAnalysisResults invalid: metrics must be a dictionary when present")
            illegal_keys = sorted(set(self.metrics).intersection(self.FORBIDDEN_METRICS_KEYS))
            if illegal_keys:
                raise RuntimeError(
                    f"RFAnalysisResults invalid: metrics contains forbidden keys {illegal_keys}"
                )

        if self.antenna_pattern is not None and not isinstance(self.antenna_pattern, dict):
            raise RuntimeError("RFAnalysisResults invalid: antenna_pattern must be a dict when present")

        if self.network_graph is not None:
            if isinstance(self.network_graph, dict):
                graph = NetworkGraph.from_dict(self.network_graph)
            elif isinstance(self.network_graph, NetworkGraph):
                graph = self.network_graph
            else:
                raise RuntimeError("RFAnalysisResults invalid: network_graph must be a NetworkGraph or dict")
            graph.validate()

        if self.network_events is not None and not isinstance(self.network_events, dict):
            raise RuntimeError("RFAnalysisResults invalid: network_events must be a dict when present")

        if self.network_evolution is not None and not isinstance(self.network_evolution, dict):
            raise RuntimeError("RFAnalysisResults invalid: network_evolution must be a dict when present")
