from __future__ import annotations

from ogn_tool.reporting.report_views import (
    get_network_risk_summary,
    get_network_status,
    get_recommended_actions,
    get_rf_signature,
    get_station_health_summary,
)


def _report() -> dict:
    return {
        'run_id': 'run-1',
        'metadata': {},
        'network_metrics': {
            'network_summary': {
                'network_status': 'WARNING',
                'critical_station_count': 1,
                'warning_station_count': 2,
                'top_critical_station': 'S1',
                'notes': 'network shows fragility',
            },
            'station_health': [
                {'station_id': 'S1', 'health_status': 'CRITICAL'},
                {'station_id': 'S2', 'health_status': 'WARNING'},
                {'station_id': 'S3', 'health_status': 'GOOD'},
            ],
            'station_dependency': [],
            'network_robustness': {'redundancy_score': 0.42, 'interpretation': 'fragile network', 'confidence_score': 0.75},
            'station_placement': {},
        },
        'coverage_score': 0.61,
    }


def test_get_network_status_returns_stable_projection() -> None:
    status = get_network_status(_report())

    assert status == {
        'network_status': 'WARNING',
        'critical_station_count': 1,
        'warning_station_count': 2,
        'top_critical_station': 'S1',
        'notes': 'network shows fragility',
    }


def test_get_station_health_summary_counts_health_states() -> None:
    summary = get_station_health_summary(_report())

    assert summary == {
        'station_count': 3,
        'critical_count': 1,
        'warning_count': 1,
        'good_count': 1,
        'critical_stations': ['S1'],
    }


def test_get_network_risk_summary_returns_report_projection() -> None:
    summary = get_network_risk_summary(_report())

    assert summary == {
        'redundancy_score': 0.42,
        'redundancy_interpretation': 'fragile network',
        'confidence_score': 0.75,
        'risk_warnings': [],
    }


def test_get_rf_signature_returns_empty_projection() -> None:
    signature = get_rf_signature(_report())
    assert signature == {}


def test_get_recommended_actions_returns_empty_projection() -> None:
    actions = get_recommended_actions(_report())
    assert actions == []


def test_report_views_require_canonical_report_type() -> None:
    try:
        get_network_status(None)
    except TypeError as exc:
        assert str(exc) == 'Expected canonical report dict'
    else:
        raise AssertionError('Expected TypeError')
