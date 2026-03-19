"""
Unit tests for temporal_observability.py
"""
import pandas as pd
from ogn_tool.intelligence.temporal.temporal_observability import compute_temporal_observability

def test_empty_window():
    result = compute_temporal_observability(pd.Series([], dtype='int64'), 24)
    assert result.hours_with_packets == 0
    assert result.data_gaps_detected
    assert result.window_coverage_ratio == 0.0

def test_full_window():
    ts = pd.Series([3600 * i for i in range(24)])  # 24h, 1/h
    result = compute_temporal_observability(ts, 24)
    assert result.hours_with_packets == 24
    assert not result.data_gaps_detected
    assert result.window_coverage_ratio == 1.0

def test_with_gaps():
    ts = pd.Series([0, 3600, 2*3600, 10*3600, 11*3600])
    result = compute_temporal_observability(ts, 12)
    assert result.max_gap_hours >= 7
    assert result.data_gaps_detected
    assert result.hours_with_packets == 5

def test_streak():
    ts = pd.Series([0, 3600, 2*3600, 3*3600, 10*3600])
    result = compute_temporal_observability(ts, 11)
    assert result.largest_active_streak_hours == 4
