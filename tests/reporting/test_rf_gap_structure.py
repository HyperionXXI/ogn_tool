from ogn_tool.reporting.report_intelligence import build_rf_gap_structure


def test_rf_gap_structure_single_cluster() -> None:
    gaps = {'gaps': [210, 240, 270], 'severity': 'low'}

    out = build_rf_gap_structure(gaps)

    assert out == {
        'clusters': [{'start': 210, 'end': 270, 'width': 90}],
        'largest_gap': 90,
        'gap_count': 1,
    }


def test_rf_gap_structure_multiple_clusters() -> None:
    gaps = {'gaps': [0, 30, 120, 150], 'severity': 'medium'}

    out = build_rf_gap_structure(gaps)

    assert out == {
        'clusters': [
            {'start': 0, 'end': 30, 'width': 60},
            {'start': 120, 'end': 150, 'width': 60},
        ],
        'largest_gap': 60,
        'gap_count': 2,
    }


def test_rf_gap_structure_wraps_across_360() -> None:
    gaps = {'gaps': [300, 330, 0, 30], 'severity': 'high'}

    out = build_rf_gap_structure(gaps)

    assert out == {
        'clusters': [{'start': 300, 'end': 30, 'width': 120}],
        'largest_gap': 120,
        'gap_count': 1,
    }


def test_rf_gap_structure_empty_input() -> None:
    assert build_rf_gap_structure({}) == {}
