
"""
Temporal observability metrics for a station RF analysis window.

Entrées :
    timestamps: pd.Series (epoch seconds)
    window_hours: float

Sortie :
    TemporalObservability (dataclass)

Mesure l'activité temporelle du flux, pas la performance RF réelle.
"""

from dataclasses import dataclass
import pandas as pd
import numpy as np

@dataclass
class TemporalObservability:
    window_hours: float
    hours_with_packets: int
    window_coverage_ratio: float
    max_gap_hours: float
    largest_active_streak_hours: float
    data_gaps_detected: bool
    packet_count: int
    packets_per_hour: float
    median_gap_hours: float
    activity_score: float

def compute_temporal_observability(
    timestamps: pd.Series,
    window_hours: float
) -> TemporalObservability:
    """
    Calcule les métriques d'observabilité temporelle d'une station RF.
    Mesure l'activité temporelle du flux, pas la performance RF réelle.
    Ajoute packet_count, packets_per_hour, median_gap_hours.
    """
    if timestamps is None or len(timestamps) == 0:
        return TemporalObservability(
            window_hours=window_hours,
            hours_with_packets=0,
            window_coverage_ratio=0.0,
            max_gap_hours=window_hours,
            largest_active_streak_hours=0.0,
            data_gaps_detected=True,
            packet_count=0,
            packets_per_hour=0.0,
            median_gap_hours=window_hours,
            activity_score=0.0,
        )
    ts = pd.to_datetime(timestamps, unit="s").sort_values()
    packet_count = len(ts)
    # hours containing packets
    hours = ts.dt.floor("H")
    hours_with_packets = hours.nunique()
    coverage_ratio = hours_with_packets / window_hours if window_hours > 0 else 0.0
    packets_per_hour = packet_count / window_hours if window_hours > 0 else 0.0
    # gaps
    gaps = ts.diff().dt.total_seconds().dropna() / 3600
    max_gap = gaps.max() if len(gaps) else 0.0
    median_gap = gaps.median() if len(gaps) else window_hours
    # longest active streak
    hour_values = hours.unique()
    hour_values = pd.Series(hour_values).sort_values()
    diffs = hour_values.diff().dt.total_seconds() / 3600
    streak = 1
    max_streak = 1
    for d in diffs.dropna():
        if d == 1:
            streak += 1
        else:
            max_streak = max(max_streak, streak)
            streak = 1
    max_streak = max(max_streak, streak)
    activity_score = float(packets_per_hour) * float(coverage_ratio)
    return TemporalObservability(
        window_hours=window_hours,
        hours_with_packets=int(hours_with_packets),
        window_coverage_ratio=float(coverage_ratio),
        max_gap_hours=float(max_gap),
        largest_active_streak_hours=float(max_streak),
        data_gaps_detected=bool(max_gap > 3),
        packet_count=packet_count,
        packets_per_hour=float(packets_per_hour),
        median_gap_hours=float(median_gap),
        activity_score=activity_score,
    )
