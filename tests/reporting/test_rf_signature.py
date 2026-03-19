from ogn_tool.reporting.report_intelligence import build_rf_signature


def test_rf_signature_basic() -> None:
    report = {
        'run_id': 'run-1',
        'metadata': {},
        'network_metrics': {
            'network_summary': {},
            'station_health': [
                {'station_id': 'S1', 'lat': 47.0, 'lon': 7.0},
                {'station_id': 'S2', 'lat': 47.1, 'lon': 7.0},
                {'station_id': 'S3', 'lat': 47.0, 'lon': 7.1},
                {'station_id': 'S4', 'lat': 46.9, 'lon': 7.0},
            ],
            'station_dependency': [],
            'network_robustness': {},
            'station_placement': {},
        },
        'coverage_score': None,
    }

    out = build_rf_signature(report)

    assert 'azimuth_coverage' in out
    assert len(out['azimuth_coverage']) == 12
    assert abs(sum(out['azimuth_coverage']) - 1.0) < 1e-9
    assert 'dominant_directions' in out
    assert 'coverage_uniformity_score' in out


def test_rf_signature_returns_empty_when_not_enough_coordinates() -> None:
    report = {
        'run_id': 'run-1',
        'metadata': {},
        'network_metrics': {
            'network_summary': {},
            'station_health': [{'station_id': 'S1', 'lat': 47.0, 'lon': 7.0}],
            'station_dependency': [],
            'network_robustness': {},
            'station_placement': {},
        },
        'coverage_score': None,
    }

    assert build_rf_signature(report) == {}
