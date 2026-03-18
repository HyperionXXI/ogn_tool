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

from ogn_tool.analysis.experimental.shadow import compute_shadow_proxy as compute_shadow_proxy

__all__ = [
    "compute_shadow_proxy",
]
