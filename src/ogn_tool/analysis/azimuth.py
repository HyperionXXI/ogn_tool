"""Legacy entry point for experimental azimuth diagnostics.

This module is retained for backwards compatibility with existing imports.
The actual implementation lives under `ogn_tool.analysis.experimental`.
"""

from .experimental.azimuth import compute_azimuth_radiation

__all__ = ["compute_azimuth_radiation"]
