from __future__ import annotations

from typing import Any

REPORT_CONTRACT_VERSION = '1.0'

REQUIRED_TOP_LEVEL_KEYS = {
    'run_id',
    'metadata',
    'network_metrics',
    'coverage_score',
}

REQUIRED_NETWORK_METRIC_KEYS = {
    'network_summary',
    'station_health',
    'station_dependency',
    'network_robustness',
    'station_placement',
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def validate_network_report_contract(contract: dict[str, Any]) -> None:
    _require(isinstance(contract, dict), 'report contract must be a dict')

    top_keys = set(contract.keys())
    _require(
        top_keys == REQUIRED_TOP_LEVEL_KEYS,
        f'invalid top-level keys: expected {sorted(REQUIRED_TOP_LEVEL_KEYS)}, got {sorted(top_keys)}',
    )

    _require(isinstance(contract['run_id'], str), 'run_id must be a string')
    _require(isinstance(contract['metadata'], dict), 'metadata must be a dict')

    network_metrics = contract['network_metrics']
    _require(isinstance(network_metrics, dict), 'network_metrics must be a dict')

    metric_keys = set(network_metrics.keys())
    _require(
        metric_keys == REQUIRED_NETWORK_METRIC_KEYS,
        f'invalid network_metrics keys: expected {sorted(REQUIRED_NETWORK_METRIC_KEYS)}, got {sorted(metric_keys)}',
    )

    _require(isinstance(network_metrics['network_summary'], dict), 'network_metrics.network_summary must be a dict')
    _require(isinstance(network_metrics['station_health'], list), 'network_metrics.station_health must be a list')
    _require(isinstance(network_metrics['station_dependency'], list), 'network_metrics.station_dependency must be a list')
    _require(isinstance(network_metrics['network_robustness'], dict), 'network_metrics.network_robustness must be a dict')
    _require(isinstance(network_metrics['station_placement'], dict), 'network_metrics.station_placement must be a dict')

    coverage_score = contract['coverage_score']
    _require(
        coverage_score is None or isinstance(coverage_score, (int, float)),
        'coverage_score must be a float or null',
    )


def export_network_report_json(contract: dict[str, Any]) -> dict[str, Any]:
    """Return canonical report.json artifact after strict contract validation."""
    validate_network_report_contract(contract)
    return contract


__all__ = [
    'REPORT_CONTRACT_VERSION',
    'validate_network_report_contract',
    'export_network_report_json',
]
