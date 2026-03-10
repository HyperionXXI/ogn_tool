"""Polar coverage analysis utilities.

This module provides utilities to summarize RF coverage in a polar (azimuthal)
format, which is useful for visualizing directional coverage and gaps.
"""

from __future__ import annotations

from typing import Any


def compute_polar_coverage(packets_rf: Any, bins: int = 36) -> list[dict]:
    """Compute polar coverage summary per azimuth sector.

    The output is a list of buckets, one per azimuth sector, where each bucket
    contains the sector center angle and basic distance statistics.

    Args:
        packets_rf: DataFrame-like object containing at least:
            - ``bearing_deg``: azimuth in degrees (0-360)
            - ``distance_km``: distance in kilometers
        bins: Number of angular sectors to divide 0-360° into.

    Returns:
        A list of dicts, each with keys:
            - ``azimuth``: center angle for the sector (degrees)
            - ``max_distance``: maximum distance seen in this sector (km)
            - ``avg_distance``: average distance in this sector (km)
            - ``packets``: number of packets in this sector
    """

    import numpy as np
    import pandas as pd

    if packets_rf is None:
        return []

    try:
        df = pd.DataFrame(packets_rf)
    except Exception:
        return []

    if df.empty:
        return []

    if "bearing_deg" not in df.columns or "distance_km" not in df.columns:
        return []

    df = df.copy()
    df["bearing_deg"] = pd.to_numeric(df["bearing_deg"], errors="coerce")
    df["distance_km"] = pd.to_numeric(df["distance_km"], errors="coerce")
    df = df.dropna(subset=["bearing_deg", "distance_km"])

    if df.empty:
        return []

    # Normalize bearings into [0, 360)
    df["bearing_deg"] = ((df["bearing_deg"] % 360) + 360) % 360

    edges = np.linspace(0.0, 360.0, bins + 1)
    # digitize returns 1..len(edges), subtract 1 to make 0-indexed
    sector_idx = np.digitize(df["bearing_deg"], edges, right=False) - 1
    sector_idx = np.clip(sector_idx, 0, bins - 1)
    df["sector"] = sector_idx

    grouped = df.groupby("sector")

    sectors: list[dict] = []
    for i in range(bins):
        sector_df = grouped.get_group(i) if i in grouped.groups else None

        if sector_df is None or sector_df.empty:
            max_distance = 0.0
            avg_distance = 0.0
            packet_count = 0
        else:
            packet_count = int(len(sector_df))
            max_distance = float(sector_df["distance_km"].max())
            avg_distance = float(sector_df["distance_km"].mean())

        sector_start = edges[i]
        sector_end = edges[i + 1]
        sector_center = (sector_start + sector_end) / 2.0

        sectors.append(
            {
                "azimuth": float(sector_center % 360.0),
                "max_distance": max_distance,
                "avg_distance": avg_distance,
                "packets": packet_count,
            }
        )

    return sectors
