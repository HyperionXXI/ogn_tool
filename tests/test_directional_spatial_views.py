from __future__ import annotations

from ogn_tool.reporting.directional_spatial_views import build_directional_sectors


def test_build_directional_sectors_returns_explicit_spatial_and_diagnostic_orderings() -> None:
    histogram = {
        'edges': [0.0, 10.0, 20.0, 30.0, 40.0],
        'hist': [2, 8, 5, 1],
    }

    sectors = build_directional_sectors(histogram)

    assert sectors['packet_count'] == 16
    assert sectors['sector_count'] == 4
    assert [sector['label'] for sector in sectors['sectors_by_weight']] == ['10°-20°', '20°-30°', '0°-10°', '30°-40°']
    assert [sector['label'] for sector in sectors['sectors_by_azimuth']] == ['0°-10°', '10°-20°', '20°-30°', '30°-40°']
    assert sectors['dominant_arc']['label'] == '0°-30°'
    assert sectors['dominant_arc']['count'] == 15


def test_build_directional_sectors_handles_empty_histogram() -> None:
    sectors = build_directional_sectors({})

    assert sectors == {
        'packet_count': 0,
        'sector_count': 0,
        'sectors_by_azimuth': [],
        'sectors_by_weight': [],
        'dominant_arc': None,
    }
