from ogn_tool.reporting.report_intelligence import build_rf_directional_gaps


def test_rf_directional_gaps_detects_low_bins() -> None:
    signature = {
        'azimuth_coverage': [0.1] * 12,
    }
    signature['azimuth_coverage'][7] = 0.01
    signature['azimuth_coverage'][8] = 0.01

    out = build_rf_directional_gaps(signature)

    assert 'gaps' in out
    assert 210 in out['gaps']
    assert 240 in out['gaps']


def test_rf_directional_gaps_empty_when_uniform() -> None:
    signature = {
        'azimuth_coverage': [1 / 12] * 12,
    }

    assert build_rf_directional_gaps(signature) == {}


def test_rf_directional_gaps_invalid_input() -> None:
    assert build_rf_directional_gaps({}) == {}
