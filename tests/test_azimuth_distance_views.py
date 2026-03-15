from __future__ import annotations

from ogn_tool.reporting.azimuth_distance_views import build_azimuth_distance_summary


SURFACE = {
    'azimuth_bins': [0.0, 90.0, 180.0],
    'distance_bins_km': [0.0, 10.0, 20.0],
    'matrix': [[1, 2], [0, 3]],
    'packet_count': 6,
}


def test_build_azimuth_distance_summary_returns_expected_projection() -> None:
    summary = build_azimuth_distance_summary(SURFACE)

    assert summary['packet_count'] == 6
    assert summary['azimuth_bin_count'] == 2
    assert summary['distance_bin_count'] == 2
    assert summary['nonzero_cell_count'] == 3
    assert summary['total_cell_count'] == 4
    assert summary['max_cell_count'] == 3
    assert summary['dominant_cell'] == {
        'azimuth_start_deg': 90.0,
        'azimuth_end_deg': 180.0,
        'distance_start_km': 10.0,
        'distance_end_km': 20.0,
        'count': 3,
    }


def test_build_azimuth_distance_summary_handles_empty_surface() -> None:
    summary = build_azimuth_distance_summary(
        {
            'azimuth_bins': [0.0],
            'distance_bins_km': [0.0],
            'matrix': [],
            'packet_count': 0,
        }
    )

    assert summary['packet_count'] == 0
    assert summary['azimuth_bin_count'] == 0
    assert summary['distance_bin_count'] == 0
    assert summary['nonzero_cell_count'] == 0
    assert summary['total_cell_count'] == 0
    assert summary['max_cell_count'] == 0
    assert summary['dominant_cell'] is None
