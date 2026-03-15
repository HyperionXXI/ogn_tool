from __future__ import annotations

from pathlib import Path

import pandas as pd

from ogn_tool.reporting.network_engineering_report import NetworkEngineeringReport
from ogn_tool.reporting.run_artifact_bundle import export_analysis_run_bundle
from ogn_tool.reporting.run_comparability import build_run_comparability
from ogn_tool.reporting.run_comparison_views import compare_run_bundles



def _build_report(*, critical_station_ids: list[str], station_count: int, redundancy_score: float, confidence_score: float) -> NetworkEngineeringReport:
    rows = []
    for index in range(station_count):
        station_id = f'S{index + 1}'
        rows.append({
            'station_id': station_id,
            'health_status': 'CRITICAL' if station_id in critical_station_ids else 'GOOD',
        })

    return NetworkEngineeringReport(
        network_summary={
            'network_status': 'WARNING' if critical_station_ids else 'GOOD',
            'critical_station_count': len(critical_station_ids),
            'warning_station_count': 0,
        },
        station_health_table=pd.DataFrame(rows),
        network_redundancy={'redundancy_score': redundancy_score, 'interpretation': 'x'},
        network_confidence={'confidence_score': confidence_score},
    )



def _build_bundle(base_dir: Path, name: str, report: NetworkEngineeringReport) -> Path:
    bundle_path = base_dir / name
    comparability = build_run_comparability(
        analysis_version='2026.03',
        time_window_start='2026-03-14T10:00:00Z',
        time_window_end='2026-03-14T11:00:00Z',
        config_identity='cfg_abc123',
    )
    export_analysis_run_bundle(
        report,
        bundle_path,
        dataset_identity={
            'dataset_id': 'dataset-001',
            'packet_count': 123,
            'time_start': '2026-03-14T10:00:00Z',
            'time_end': '2026-03-14T11:00:00Z',
            'source': 'ogn_sqlite',
        },
        comparability=comparability,
    )
    return bundle_path



def test_compare_run_bundles_marks_identical_runs_comparable(tmp_path: Path) -> None:
    report = _build_report(critical_station_ids=['S1'], station_count=2, redundancy_score=0.5, confidence_score=0.8)
    left_bundle = _build_bundle(tmp_path, 'left', report)
    right_bundle = _build_bundle(tmp_path, 'right', report)

    comparison = compare_run_bundles(left_bundle, right_bundle)

    assert comparison['comparability']['is_comparable'] is True
    assert comparison['summary_delta']['redundancy_score']['delta'] == 0.0



def test_compare_run_bundles_detects_topology_change(tmp_path: Path) -> None:
    left_bundle = _build_bundle(
        tmp_path,
        'left',
        _build_report(critical_station_ids=['S1'], station_count=2, redundancy_score=0.5, confidence_score=0.8),
    )
    right_bundle = _build_bundle(
        tmp_path,
        'right',
        _build_report(critical_station_ids=['S1', 'S2'], station_count=3, redundancy_score=0.4, confidence_score=0.8),
    )

    comparison = compare_run_bundles(left_bundle, right_bundle)

    assert comparison['topology_delta']['new_critical_stations'] == ['S2']
    assert comparison['summary_delta']['station_count']['delta'] == 1.0



def test_compare_run_bundles_allows_temporal_comparison_with_different_dataset_identity(tmp_path: Path) -> None:
    report = _build_report(critical_station_ids=[], station_count=1, redundancy_score=0.6, confidence_score=0.8)
    left_bundle = tmp_path / 'left'
    right_bundle = tmp_path / 'right'

    comparability = build_run_comparability(
        analysis_version='2026.03',
        time_window_start='2026-03-14T10:00:00Z',
        time_window_end='2026-03-14T11:00:00Z',
        config_identity='cfg_abc123',
    )
    export_analysis_run_bundle(
        report,
        left_bundle,
        dataset_identity={'dataset_id': 'dataset-001', 'packet_count': 1, 'time_start': None, 'time_end': None, 'source': 'ogn_sqlite'},
        comparability=comparability,
    )
    export_analysis_run_bundle(
        report,
        right_bundle,
        dataset_identity={'dataset_id': 'dataset-002', 'packet_count': 1, 'time_start': None, 'time_end': None, 'source': 'ogn_sqlite'},
        comparability=comparability,
    )

    comparison = compare_run_bundles(left_bundle, right_bundle)

    assert comparison['comparability']['dataset_identity_match'] is False
    assert comparison['comparability']['is_comparable'] is True
    assert comparison['interpretation']['network_trend'] == 'stable'
