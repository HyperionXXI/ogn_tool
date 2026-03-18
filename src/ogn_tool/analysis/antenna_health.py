"""Legacy entry point for experimental antenna diagnostics.

This module is retained for backwards compatibility with existing imports.
The actual implementation lives under `ogn_tool.analysis.experimental`.
"""

from ogn_tool._legacy.analysis.experimental.antenna_health import analyze

__all__ = ["analyze"]
