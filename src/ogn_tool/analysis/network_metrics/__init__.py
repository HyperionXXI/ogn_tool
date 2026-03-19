"""Network-level metrics derived from graph structures.

This package contains computations that derive quantitative metrics
from the network topology and RF analysis results.

Typical responsibilities
------------------------
- station influence metrics
- network robustness indicators
- coverage-related statistics
- dependency metrics

Inputs:
    graph structures from ogn_tool.kernel

Outputs:
    structured metrics used by reporting and intelligence layers.

This package does not build graphs itself.
"""

from ogn_tool.kernel.station_metrics import (
    build_station_metrics,
    build_station_reception,
    compute_station_overlap,
    station_aircraft_matrix,
    station_metrics,
    station_overlap,
)
from ogn_tool.kernel.coverage_metrics import (
    aircraft_redundancy,
    build_network_metrics,
    build_reception_events,
    compute_blind_zones,
    compute_coverage_redundancy,
    detect_network_blind_zones,
    enrich_coverage_grid,
)
from ogn_tool.kernel.visibility_metrics import (
    build_visibility_matrix,
    compute_station_dependency,
    compute_visibility_metrics,
    compute_visibility_overlap,
    compute_visibility_redundancy,
    compute_visibility_summary,
)
from ogn_tool.intelligence.network.station_influence import compute_station_influence
from ogn_tool.intelligence.network.station_anomaly_detection import detect_station_anomalies
from ogn_tool.intelligence.network.network_robustness_metrics import compute_station_removal_impact
from ogn_tool.intelligence.network.station_placement_planner import compute_optimal_station_locations, extract_fragile_aircraft

__all__ = [
    "build_network_metrics",
    "build_reception_events",
    "build_station_metrics",
    "build_station_reception",
    "compute_blind_zones",
    "compute_coverage_redundancy",
    "compute_station_overlap",
    "station_aircraft_matrix",
    "station_metrics",
    "station_overlap",
    "aircraft_redundancy",
    "detect_network_blind_zones",
    "enrich_coverage_grid",
    "build_visibility_matrix",
    "compute_station_dependency",
    "compute_visibility_metrics",
    "compute_visibility_overlap",
    "compute_visibility_redundancy",
    "compute_visibility_summary",
    "compute_station_influence",
    "detect_station_anomalies",
    "compute_station_removal_impact",
    "compute_optimal_station_locations",
    "extract_fragile_aircraft",
]
