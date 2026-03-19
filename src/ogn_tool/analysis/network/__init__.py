"""High-level network synthesis and summaries.

This package contains orchestration logic and synthesized views
of the analyzed RF network.

Responsibilities
----------------
- combine graph and metric outputs
- produce network-level summaries
- support reporting layers

Typical outputs:
- network health summaries
- synthesized network diagnostics
- aggregated results for reporting

This layer sits above:

    ogn_tool.kernel
    ogn_tool.analysis.network_metrics
"""

from ogn_tool.intelligence.network.network_topology_inference import compute_network_topology, compute_station_roles, compute_coverage_redundancy
from .station_range import analyze as analyze_station_range
from .station_quality import analyze as analyze_station_quality
from ogn_tool.intelligence.network.station_compare_analysis import analyze as analyze_station_compare

__all__ = [
    "compute_network_topology",
    "compute_station_roles",
    "compute_coverage_redundancy",
    "analyze_station_range",
    "analyze_station_quality",
    "analyze_station_compare",
]
