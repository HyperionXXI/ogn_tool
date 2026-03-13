"""Shared contracts for the intelligence layer.

The intelligence layer consumes canonical outputs from
`analysis/network_metrics` and related analytical layers.
It must not recompute RF or network metrics, rebuild network graphs,
or access raw datasets directly.
"""

from typing import TypeAlias

NetworkMetrics: TypeAlias = dict[str, object]


def ensure_metrics(metrics: NetworkMetrics | None) -> NetworkMetrics:
    """Return an empty metrics dict when the caller passes None."""
    return metrics or {}
