"""Legacy entry point for experimental shadow diagnostics.

This module is retained for backwards compatibility with existing imports.
The actual implementation lives under `ogn_tool.analysis.experimental`.
"""

from .experimental.shadow import compute_shadow_proxy

__all__ = ["compute_shadow_proxy"]
