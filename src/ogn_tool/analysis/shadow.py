"""Legacy entry point for experimental shadow diagnostics.

This module is retained for backwards compatibility with existing imports.
The actual implementation lives under `ogn_tool.analysis.experimental`.
"""

from .experimental.shadow import compute_shadow_proxy


def detect_rf_shadows(df, azimuth_histogram=None):
    """
    Compatibility wrapper used by RFAnalysisEngine.

    Uses the experimental shadow proxy internally.
    """
    if df is None or len(df) == 0:
        return {"shadow_sectors": []}

    try:
        result = compute_shadow_proxy(df)
    except Exception:
        return {"shadow_sectors": []}

    return result


__all__ = [
    "compute_shadow_proxy",
    "detect_rf_shadows",
]
