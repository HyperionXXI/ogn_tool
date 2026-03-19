from ogn_tool.reporting.report_intelligence import build_report_intelligence


def test_intelligence_detects_critical_station() -> None:
    report = {
        'run_id': 'run-1',
        'metadata': {},
        'network_metrics': {
            'network_summary': {},
            'station_health': [
                {'station_id': 'S1', 'health_status': 'CRITICAL'}
            ],
            'station_dependency': [],
            'network_robustness': {'redundancy_score': 0.3},
            'station_placement': {},
        },
        'coverage_score': None,
    }

    out = build_report_intelligence(report)

    assert len(out['alerts']) == 1
    assert out['alerts'][0]['type'] == 'critical_station'
    assert out['rf_analysis'] == {
        'rf_signature_version': 'v1',
        'rf_signature': {},
    }


def test_intelligence_builds_recommendations_and_diagnostics() -> None:
    report = {
        'run_id': 'run-1',
        'metadata': {},
        'network_metrics': {
            'network_summary': {},
            'station_health': [],
            'station_dependency': [],
            'network_robustness': {'redundancy_score': 0.2, 'confidence_score': 0.3},
            'station_placement': {},
        },
        'coverage_score': 0.5,
    }

    out = build_report_intelligence(report)

    assert any(item['type'] == 'network_fragility' for item in out['diagnostics'])
    assert any(item['type'] == 'low_confidence' for item in out['diagnostics'])
    assert any(item['type'] == 'increase_redundancy' for item in out['recommended_actions'])
    assert out['rf_analysis'] == {
        'rf_signature_version': 'v1',
        'rf_signature': {},
    }
