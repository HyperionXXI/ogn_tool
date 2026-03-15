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
    assert summary['azimuth_profile'] == [
        {'azimuth_start_deg': 0.0, 'azimuth_end_deg': 90.0, 'count': 3, 'share': 0.5},
        {'azimuth_start_deg': 90.0, 'azimuth_end_deg': 180.0, 'count': 3, 'share': 0.5},
    ]
    assert summary['distance_profile'] == [
        {'distance_start_km': 0.0, 'distance_end_km': 10.0, 'count': 1, 'share': 1.0 / 6.0},
        {'distance_start_km': 10.0, 'distance_end_km': 20.0, 'count': 5, 'share': 5.0 / 6.0},
    ]
    assert summary['rf_signature'] == {
        'packet_count': 6,
        'dominant_corridor_start_deg': 0.0,
        'dominant_corridor_end_deg': 180.0,
        'corridor_width_deg': 180.0,
        'dominant_corridor_share': 1.0,
        'dominant_distance_band_km': [10.0, 20.0],
        'dominant_distance_band_share': 5.0 / 6.0,
        'nonzero_distance_band_count': 2,
        'distance_spread_index': 1.0,
        'anisotropy_index': 1.0,
        'interpretation': 'directional traffic corridor likely',
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
    assert summary['azimuth_profile'] == []
    assert summary['distance_profile'] == []
    assert summary['rf_signature'] is None
