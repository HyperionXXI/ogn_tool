from __future__ import annotations

from ogn_tool.reporting.report_export import (
    export_network_report_json,
    validate_network_report_contract,
)


def _valid_contract() -> dict:
    return {
        'run_id': 'run-001',
        'metadata': {'station_id': 'FK50887'},
        'network_metrics': {
            'network_summary': {'packet_count': 10},
            'station_health': [],
            'station_dependency': [],
            'network_robustness': {},
            'station_placement': {},
        },
        'coverage_score': 0.5,
    }


def test_export_network_report_json_structure() -> None:
    contract = _valid_contract()

    data = export_network_report_json(contract)

    assert set(data.keys()) == {'run_id', 'metadata', 'network_metrics', 'coverage_score'}
    assert set(data['network_metrics'].keys()) == {
        'network_summary',
        'station_health',
        'station_dependency',
        'network_robustness',
        'station_placement',
    }


def test_validate_network_report_contract_accepts_valid_contract() -> None:
    validate_network_report_contract(_valid_contract())


def test_export_network_report_type_validation() -> None:
    try:
        export_network_report_json(None)  # type: ignore[arg-type]
    except RuntimeError as exc:
        assert str(exc) == 'report contract must be a dict'
    else:
        raise AssertionError('Expected RuntimeError when contract is invalid')


def test_report_rejects_extra_top_level_keys() -> None:
    contract = _valid_contract()
    contract['legacy'] = {}

    try:
        validate_network_report_contract(contract)
    except RuntimeError as exc:
        assert 'invalid top-level keys' in str(exc)
    else:
        raise AssertionError('Expected RuntimeError when top-level keys are invalid')


def test_report_rejects_missing_network_metrics_keys() -> None:
    contract = _valid_contract()
    del contract['network_metrics']['station_placement']

    try:
        validate_network_report_contract(contract)
    except RuntimeError as exc:
        assert 'invalid network_metrics keys' in str(exc)
    else:
        raise AssertionError('Expected RuntimeError when network_metrics keys are invalid')
