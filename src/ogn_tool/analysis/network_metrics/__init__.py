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
    graph structures from ogn_tool.analysis.network_graph

Outputs:
    structured metrics used by reporting and intelligence layers.

This package does not build graphs itself.
"""

from .station_metrics import (
    build_station_metrics,
    build_station_reception,
    compute_station_overlap,
    station_aircraft_matrix,
    station_metrics,
    station_overlap,
)
from .coverage_metrics import (
    aircraft_redundancy,
    build_network_metrics,
    build_reception_events,
    compute_blind_zones,
    compute_coverage_redundancy,
    detect_network_blind_zones,
    enrich_coverage_grid,
)
from .visibility import (
    build_visibility_matrix,
    compute_station_dependency,
    compute_visibility_metrics,
    compute_visibility_overlap,
    compute_visibility_redundancy,
    compute_visibility_summary,
)
from .station_influence import compute_station_influence
from .station_anomaly import detect_station_anomalies
from .network_robustness import compute_station_removal_impact
from .station_placement import compute_optimal_station_locations, extract_fragile_aircraft

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
