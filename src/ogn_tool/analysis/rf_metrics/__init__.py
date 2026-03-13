"""RF metrics analysis package."""

from .rf_statistics import (
    compute_altitude_delta,
    compute_bearing,
    compute_distance,
    compute_distance_bearing,
    summarize_observation_vectors,
    summarize_signal_quality,
)

__all__ = [
    "compute_altitude_delta",
    "compute_bearing",
    "compute_distance",
    "compute_distance_bearing",
    "summarize_observation_vectors",
    "summarize_signal_quality",
]

from .directional_analysis import build_directional_diagnostics

__all__ = list(dict.fromkeys(__all__ + ["build_directional_diagnostics"]))
