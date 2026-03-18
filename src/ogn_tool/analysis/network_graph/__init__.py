"""Network graph construction layer.

This package contains the topology layer of the RF network analysis.

Responsibilities
----------------
- Build graph representations of the station network
- Compute connectivity relationships
- Represent dependencies between stations
- Provide graph structures used by higher-level metrics

This layer focuses only on topology construction.

It does NOT compute:
- RF metrics
- station health scores
- network summaries

Those belong to:
    ogn_tool.analysis.network_metrics
    ogn_tool.analysis.network
"""

from ogn_tool.kernel.coverage_graph import build_coverage_graph
from .network_events import detect_coverage_regressions, detect_network_anomalies, detect_station_outages
from ogn_tool.kernel.graph_metrics import compute_graph_metrics, compute_network_evolution_metrics
from .network_optimization import estimate_station_gain, optimize_station_locations, suggest_station_locations
from .network_timeseries import compute_coverage_timeseries, compute_network_load_timeseries, compute_station_activity_timeseries
from ogn_tool.kernel.rf_graph_builder import build_rf_graph
from ogn_tool.kernel.station_graph import compute_station_aircraft_links

__all__ = [
    "build_rf_graph",
    "compute_station_aircraft_links",
    "build_coverage_graph",
    "compute_graph_metrics",
    "compute_network_evolution_metrics",
    "optimize_station_locations",
    "estimate_station_gain",
    "suggest_station_locations",
    "compute_station_activity_timeseries",
    "compute_network_load_timeseries",
    "compute_coverage_timeseries",
    "detect_station_outages",
    "detect_coverage_regressions",
    "detect_network_anomalies",
]
