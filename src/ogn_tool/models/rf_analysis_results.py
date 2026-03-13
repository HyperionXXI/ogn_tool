from dataclasses import dataclass
from typing import Any, Optional

from .network_graph_model import NetworkGraph


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

    def validate(self) -> None:
        if self.metrics is not None and not isinstance(self.metrics, dict):
            raise RuntimeError("RFAnalysisResults invalid: metrics must be a dictionary when present")

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
