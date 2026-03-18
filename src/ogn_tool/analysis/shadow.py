"""Shadow analysis utilities.

Note:
Parts of this logic overlap with newer implementations in:

    rf_metrics.blind_zone_detection
    rf_metrics.probability_field

These modules are kept for compatibility with early analysis tools.
"""

from ogn_tool._legacy.analysis.experimental.shadow import compute_shadow_proxy



def detect_rf_shadows(df, azimuth_histogram=None, directional_balance=None, station_lat=None, station_lon=None):
    """Compatibility wrapper used by RFAnalysisEngine.

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
