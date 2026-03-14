from __future__ import annotations

import pandas as pd

from .network_engineering_report_builder import build_network_engineering_report as _build_canonical_report



def _extract_network_metrics(results):
    if isinstance(results, dict):
        metrics = results.get('network_metrics', {})
    else:
        metrics = getattr(results, 'network_metrics', {})
    return metrics if isinstance(metrics, dict) else {}



def _extract_spatial_observations(results):
    if isinstance(results, dict):
        value = results.get('spatial_observations')
    else:
        value = getattr(results, 'spatial_observations', None)
    return value if isinstance(value, pd.DataFrame) else None



def build_network_engineering_report(results, spatial_observations=None):
    """Compatibility wrapper around the canonical network engineering report builder."""
    metrics = _extract_network_metrics(results)
    spatial_frame = spatial_observations if spatial_observations is not None else _extract_spatial_observations(results)
    return _build_canonical_report(metrics, spatial_frame)


__all__ = ['build_network_engineering_report']
