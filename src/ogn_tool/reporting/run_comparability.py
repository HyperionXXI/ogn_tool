from __future__ import annotations

from datetime import datetime, timezone

RUN_COMPARABILITY_SCHEMA_VERSION = '1.0'



def _normalize_utc_timestamp(value: str | None) -> str | None:
    if value is None:
        return None

    parsed = datetime.fromisoformat(str(value).replace('Z', '+00:00'))
    normalized = parsed.astimezone(timezone.utc)
    return normalized.isoformat(timespec='seconds').replace('+00:00', 'Z')



def build_run_comparability(
    *,
    analysis_version: str,
    time_window_start: str | None,
    time_window_end: str | None,
    config_identity: str,
) -> dict:
    """Build a stable comparability block for exported run artifacts."""
    normalized_start = _normalize_utc_timestamp(time_window_start)
    normalized_end = _normalize_utc_timestamp(time_window_end)

    duration = None
    if normalized_start is not None and normalized_end is not None:
        start = datetime.fromisoformat(normalized_start.replace('Z', '+00:00'))
        end = datetime.fromisoformat(normalized_end.replace('Z', '+00:00'))
        if end < start:
            raise ValueError('time_window_end must be >= time_window_start')
        duration = int((end - start).total_seconds())

    return {
        'schema_version': RUN_COMPARABILITY_SCHEMA_VERSION,
        'analysis_version': str(analysis_version),
        'time_window_start': normalized_start,
        'time_window_end': normalized_end,
        'time_window_duration_s': duration,
        'config_identity': str(config_identity),
    }


__all__ = ['RUN_COMPARABILITY_SCHEMA_VERSION', 'build_run_comparability']
