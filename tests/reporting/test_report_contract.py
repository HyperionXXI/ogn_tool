from __future__ import annotations

import pandas as pd

from ogn_tool.reporting.network_engineering_report_builder import build_network_report_contract
from ogn_tool.reporting.views.dashboard_views import build_dashboard_payload


def test_build_network_report_contract_shape() -> None:
    contract = build_network_report_contract(
        run_id='run-1',
        metadata={'station_id': 'FK50887'},
        network_summary={'network_status': 'GOOD'},
        station_health=pd.DataFrame([{'station_id': 'S1', 'health_status': 'GOOD'}]),
        station_dependency=pd.DataFrame([{'station_id': 'S1', 'depends_on_station': 'S2'}]),
        network_robustness={'score': 0.9},
        station_placement={'suggestions': []},
        coverage_score=0.42,
    )

    assert set(contract.keys()) == {'run_id', 'metadata', 'network_metrics', 'coverage_score'}
    assert set(contract['network_metrics'].keys()) == {
        'network_summary',
        'station_health',
        'station_dependency',
        'network_robustness',
        'station_placement',
    }


def test_dashboard_payload_direct_contract_mapping() -> None:
    report = {
        'run_id': 'run-1',
        'metadata': {'station_id': 'FK50887'},
        'network_metrics': {
            'network_summary': {'packet_count': 12},
            'station_health': [{'station_id': 'S1', 'health_status': 'GOOD'}],
            'station_dependency': [],
            'network_robustness': {},
            'station_placement': {},
        },
        'coverage_score': 0.66,
    }

    payload = build_dashboard_payload(report)

    assert payload['network_summary']['packet_count'] == 12
    assert payload['network_summary']['coverage_score'] == 0.66
    assert payload['network_summary']['station_count'] == 1
    assert payload['stations'] == [{'station_id': 'S1', 'health_status': 'GOOD'}]
    assert payload['intelligence'] == {
        'diagnostics': [
            {
                'type': 'network_fragility',
                'severity': 'warning',
                'message': 'Low network redundancy detected',
                'redundancy_score': 0.0,
                'confidence': 0.0,
            },
            {
                'type': 'low_confidence',
                'severity': 'warning',
                'message': 'Low confidence in analysis results',
                'confidence': 0.0,
            },
        ],
        'alerts': [],
        'recommended_actions': [
            {
                'type': 'increase_redundancy',
                'priority': 'high',
                'message': 'Consider adding additional stations to improve redundancy',
            }
        ],
    }
    assert payload['debug']['run_id'] == 'run-1'
