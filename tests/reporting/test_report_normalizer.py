from ogn_tool.reporting.report_normalizer import build_ui_artifact


def _canonical_report():
    return {
        'run_id': 'run-001',
        'metadata': {},
        'network_metrics': {
            'network_summary': {'network_status': 'OK', 'confidence_score': 0.9},
            'station_health': [
                {'station_id': 'S1', 'health_status': 'GOOD', 'lat': 47.0, 'lon': 7.0},
                {'station_id': 'S2', 'health_status': 'WARNING'},
            ],
            'station_dependency': [{'station_id': 'S1', 'dependency_strength': 0.1}],
            'network_robustness': {'redundancy_score': 0.8},
            'station_placement': {},
        },
        'coverage_score': 0.75,
    }


def _metadata():
    return {
        'dataset': {'station_id': 'S1'},
        'comparability': {
            'time_window_start': '2026-03-14T10:00:00Z',
            'time_window_end': '2026-03-14T11:00:00Z',
            'time_window_duration_s': 3600,
        },
    }


def test_build_ui_artifact_canonical_only() -> None:
    out = build_ui_artifact(_canonical_report(), _metadata())

    assert out['meta']['station_id'] == 'S1'
    assert out['network']['summary']['network_status'] == 'OK'
    assert out['network']['health'][0]['station_id'] == 'S1'
    assert out['network']['dependency'][0]['station_id'] == 'S1'
    assert out['layers']['stations'][0]['station_id'] == 'S1'
    assert out['diagnostics'] == []


def test_build_ui_artifact_requires_canonical_network_metrics() -> None:
    report = _canonical_report()
    del report['network_metrics']['station_health']

    try:
        build_ui_artifact(report, _metadata())
    except RuntimeError as exc:
        assert 'station_health' in str(exc)
    else:
        raise AssertionError('Expected RuntimeError for non-canonical report')


def test_build_ui_artifact_requires_metadata_dataset_station() -> None:
    metadata = _metadata()
    metadata['dataset']['station_id'] = ''

    try:
        build_ui_artifact(_canonical_report(), metadata)
    except RuntimeError as exc:
        assert 'station_id' in str(exc)
    else:
        raise AssertionError('Expected RuntimeError for invalid metadata')
