from ogn_tool.reporting.report_intelligence import build_rf_shadow_analysis


def test_rf_shadow_analysis_empty_when_uniform_or_missing() -> None:
    assert build_rf_shadow_analysis({}, {}) == {}

    signature = {
        'coverage_uniformity_score': 0.8,
    }
    gaps = {'gaps': [210, 240], 'severity': 'low'}
    assert build_rf_shadow_analysis(signature, gaps) == {}


def test_rf_shadow_analysis_detects_shadow_when_low_uniformity_and_gaps() -> None:
    signature = {
        'coverage_uniformity_score': 0.3,
    }
    gaps = {'gaps': [210, 240, 270], 'severity': 'medium'}

    out = build_rf_shadow_analysis(signature, gaps)

    assert out['suspected'] is True
    assert out['directions'] == [210, 240, 270]
    assert 0.0 <= out['confidence'] <= 1.0


def test_rf_shadow_analysis_confidence_is_bounded() -> None:
    signature = {
        'coverage_uniformity_score': -2.0,
    }
    gaps = {'gaps': [0] * 12, 'severity': 'high'}

    out = build_rf_shadow_analysis(signature, gaps)

    assert out['confidence'] == 1.0
