from typing import TypeAlias

NetworkMetrics: TypeAlias = dict[str, object]


def ensure_metrics(metrics: NetworkMetrics | None) -> NetworkMetrics:
    """Return an empty metrics dict when the caller passes None."""
    return metrics or {}
