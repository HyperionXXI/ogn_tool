from __future__ import annotations

import pandas as pd

from ogn_tool.reporting.network_engineering_report import NetworkEngineeringReport
from ogn_tool.reporting.report_views import (
    get_network_risk_summary,
    get_network_status,
    get_recommended_actions,
    get_station_health_summary,
)



def test_get_network_status_returns_stable_projection() -> None:
    report = NetworkEngineeringReport(
        network_summary={
            'network_status': 'WARNING',
            'critical_station_count': 1,
            'warning_station_count': 2,
            'top_critical_station': 'S1',
            'notes': 'network shows fragility',
        },
        input_warnings=['warning-a'],
    )

    status = get_network_status(report)

    assert status == {
        'network_status': 'WARNING',
        'critical_station_count': 1,
        'warning_station_count': 2,
        'top_critical_station': 'S1',
        'notes': 'network shows fragility',
        'input_warnings': ['warning-a'],
    }



def test_get_station_health_summary_counts_health_states() -> None:
    report = NetworkEngineeringReport(
        station_health_table=pd.DataFrame([
            {'station_id': 'S1', 'health_status': 'CRITICAL'},
            {'station_id': 'S2', 'health_status': 'WARNING'},
            {'station_id': 'S3', 'health_status': 'GOOD'},
        ])
    )

    summary = get_station_health_summary(report)

    assert summary == {
        'station_count': 3,
        'critical_count': 1,
        'warning_count': 1,
        'good_count': 1,
        'critical_stations': ['S1'],
    }



def test_get_network_risk_summary_returns_report_projection() -> None:
    report = NetworkEngineeringReport(
        network_redundancy={'redundancy_score': 0.42, 'interpretation': 'fragile network'},
        network_confidence={'confidence_score': 0.75},
        input_warnings=['warning-a'],
    )

    summary = get_network_risk_summary(report)

    assert summary == {
        'redundancy_score': 0.42,
        'redundancy_interpretation': 'fragile network',
        'confidence_score': 0.75,
        'risk_warnings': ['warning-a'],
    }



def test_get_recommended_actions_returns_copy() -> None:
    report = NetworkEngineeringReport(recommended_actions=['action-a'])

    actions = get_recommended_actions(report)
    actions.append('action-b')

    assert report.recommended_actions == ['action-a']


def test_report_views_require_canonical_report_type() -> None:
    try:
        get_network_status(None)
    except TypeError as exc:
        assert str(exc) == 'Expected NetworkEngineeringReport'
    else:
        raise AssertionError('Expected TypeError')
