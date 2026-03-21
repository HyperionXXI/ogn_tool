"""Utilities for building a stable identity for analyzed datasets."""

from __future__ import annotations

from hashlib import sha256



def build_dataset_identity(
    packet_count: int,
    time_start: str | None,
    time_end: str | None,
    source: str,
) -> dict:
    """Build a deterministic identity record for an analysis dataset.

    The dataset identifier is derived only from stable caller-provided inputs so
    that repeated runs over the same logical dataset produce the same identity.
    """
    safe_source = str(source)
    safe_packet_count = int(packet_count)
    safe_time_start = str(time_start) if time_start is not None else None
    safe_time_end = str(time_end) if time_end is not None else None

    dataset_key = f"{safe_source}|{safe_packet_count}|{safe_time_start}|{safe_time_end}"
    dataset_id = sha256(dataset_key.encode('utf-8')).hexdigest()[:16]

    return {
        'dataset_id': dataset_id,
        'packet_count': safe_packet_count,
        'time_start': safe_time_start,
        'time_end': safe_time_end,
        'source': safe_source,
    }


__all__ = ['build_dataset_identity']
