from __future__ import annotations

from ogn_tool.reporting.directional_views import (
    build_directional_summary,
    compute_dominant_arc,
    compute_top_sectors,
    format_directional_summary,
)


def test_compute_dominant_arc_wraps_across_zero_degrees() -> None:
    edges = [0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0]
    hist = [5, 1, 1, 1, 10, 20]

    arc = compute_dominant_arc(edges, hist, packet_count=sum(hist), width_bins=3)

    assert arc is not None
    assert arc['start_bin'] == 4
    assert arc['label'] == '40°-10°'
    assert arc['count'] == 35
    assert arc['share'] == 0.9211


def test_compute_top_sectors_orders_bins_by_count() -> None:
    edges = [0.0, 10.0, 20.0, 30.0, 40.0]
    hist = [1, 7, 3, 5]

    sectors = compute_top_sectors(edges, hist, packet_count=sum(hist), top_k=3)

    assert [sector['count'] for sector in sectors] == [7, 5, 3]
    assert [sector['label'] for sector in sectors] == ['10°-20°', '30°-40°', '20°-30°']


def test_build_directional_summary_returns_expected_human_surface() -> None:
    histogram = {
        'edges': [0.0, 10.0, 20.0, 30.0, 40.0],
        'hist': [2, 8, 5, 1],
    }

    summary = build_directional_summary(
        histogram,
        0.88,
        run_id='fk50887_demo',
        station_angular_entropy={},
        shadow_risk_scores={},
    )

    assert summary['run_id'] == 'fk50887_demo'
    assert summary['packet_count'] == 16
    assert summary['coverage'] == 'broad'
    assert summary['top_bin']['label'] == '10°-20°'
    assert summary['top_bin']['share'] == 0.5
    assert summary['dominant_arc']['label'] == '0°-30°'
    assert summary['dominant_arc']['count'] == 15
    assert summary['dominant_arc_share'] == 0.9375
    assert [sector['label'] for sector in summary['top_sectors']] == ['10°-20°', '20°-30°', '0°-10°']
    assert summary['interpretation']['anisotropy'] == 'broad'
    assert summary['interpretation']['dominant_sector_strength'] == 'very concentrated'
    assert summary['interpretation']['hard_shadow_detected'] is False
    assert summary['interpretation']['confidence'] == 'low'


def test_build_directional_summary_handles_missing_histogram() -> None:
    summary = build_directional_summary({}, None)

    assert summary['packet_count'] == 0
    assert summary['coverage'] == 'unknown'
    assert summary['top_bin'] is None
    assert summary['dominant_arc'] is None
    assert summary['top_sectors'] == []
    assert summary['interpretation']['summary_sentence'] == 'Directional coverage summary is unavailable.'
    assert summary['interpretation']['confidence'] == 'low'


def test_format_directional_summary_includes_key_sections() -> None:
    histogram = {
        'edges': [0.0, 10.0, 20.0, 30.0, 40.0],
        'hist': [2, 8, 5, 1],
    }
    summary = build_directional_summary(histogram, 0.88)

    rendered = format_directional_summary(summary)

    assert 'Directional summary' in rendered
    assert 'Packets analysed: 16' in rendered
    assert 'Dominant arc: 0°-30°' in rendered
    assert 'Top sectors:' in rendered
    assert 'Top bin (debug): 10°-20° (8 packets, 50.0%)' in rendered
    assert 'Hard shadow detected: no' in rendered
