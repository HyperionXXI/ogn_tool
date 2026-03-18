"""Experimental RF analysis modules.

This namespace contains research prototypes and algorithms that are not
part of the stable analysis pipeline.

Modules here may:

    - change without notice
    - move into canonical packages later
    - be removed if superseded

Canonical layers are:

    rf_models
    rf_metrics
    network_graph
    network_metrics
    intelligence
"""

from ogn_tool.analysis.experimental.antenna_health import analyze as analyze_antenna_health
from ogn_tool.analysis.experimental.azimuth import compute_azimuth_radiation as compute_azimuth_radiation
from ogn_tool.analysis.experimental.shadow import compute_shadow_proxy as compute_shadow_proxy

__all__ = [
    "analyze_antenna_health",
    "compute_azimuth_radiation",
    "compute_shadow_proxy",
]
