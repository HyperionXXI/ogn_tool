from __future__ import annotations

from pathlib import Path

import pandas as pd

from ogn_tool.reporting.network_engineering_report import NetworkEngineeringReport
from ogn_tool.reporting.run_artifact_bundle import export_analysis_run_bundle
from ogn_tool.reporting.run_comparability import build_run_comparability
from ogn_tool.reporting.run_evolution_views import compute_network_evolution
from ogn_tool.reporting.run_registry import register_run



def _build_report(*, critical_station_count: int, redundancy_score: float, confidence_score: float) -> NetworkEngineeringReport:
    rows = [
        {
            'station_id': f'S{index + 1}',
            'health_status': 'CRITICAL' if index < critical_station_count else 'GOOD',
        }
        for index in range(max(critical_station_count, 1))
    ]
    critical_ids = [row['station_id'] for row in rows if row['health_status'] == 'CRITICAL']
    return NetworkEngineeringReport(
        network_summary={
            'network_status': 'WARNING' if critical_ids else 'GOOD',
            'critical_station_count': len(critical_ids),
            'warning_station_count': 0,
        },
        station_health_table=pd.DataFrame(rows),
        network_redundancy={'redundancy_score': redundancy_score, 'interpretation': 'x'},
        network_confidence={'confidence_score': confidence_score},
    )



def _register_bundle(
    tmp_path: Path,
    registry_dir: Path,
    *,
    run_name: str,
    analysis_version: str = '2026.03',
    config_identity: str = 'cfg_abc123',
    dataset_id: str = 'dataset-001',
    critical_station_count: int,
    redundancy_score: float,
    confidence_score: float,
) -> None:
    bundle_path = tmp_path / run_name
    export_analysis_run_bundle(
        _build_report(
            critical_station_count=critical_station_count,
            redundancy_score=redundancy_score,
            confidence_score=confidence_score,
        ),
        bundle_path,
        dataset_identity={
            'dataset_id': dataset_id,
            'packet_count': 123,
            'time_start': '2026-03-14T10:00:00Z',
            'time_end': '2026-03-14T11:00:00Z',
            'source': 'ogn_sqlite',
        },
        comparability=build_run_comparability(
            analysis_version=analysis_version,
            time_window_start='2026-03-14T10:00:00Z',
            time_window_end='2026-03-14T11:00:00Z',
            config_identity=config_identity,
        ),
    )
    register_run(bundle_path, registry_dir)



def test_compute_network_evolution_handles_empty_registry(tmp_path: Path) -> None:
    evolution = compute_network_evolution(tmp_path / 'analysis_runs')

    assert evolution == {
        'runs': [],
        'lineage': {
            'consistent': True,
            'breakpoints': [],
            'reason': None,
        },
        'metrics_timeline': {
            'redundancy_score': [],
            'critical_station_count': [],
            'confidence_score': [],
        },
        'events': [],
        'trend': {
            'network_redundancy': 'stable',
            'network_health': 'stable',
        },
    }



def test_compute_network_evolution_builds_timeline_and_trends(tmp_path: Path) -> None:
    registry_dir = tmp_path / 'analysis_runs'
    _register_bundle(tmp_path, registry_dir, run_name='run_001', critical_station_count=2, redundancy_score=0.4, confidence_score=0.7)
    _register_bundle(tmp_path, registry_dir, run_name='run_002', critical_station_count=1, redundancy_score=0.6, confidence_score=0.7)

    evolution = compute_network_evolution(registry_dir)

    assert evolution['runs'] == ['run_001', 'run_002']
    assert evolution['lineage']['consistent'] is True
    assert evolution['metrics_timeline']['redundancy_score'] == [
        {'run': 'run_001', 'value': 0.4},
        {'run': 'run_002', 'value': 0.6},
    ]
    assert evolution['trend']['network_redundancy'] == 'improving'
    assert evolution['trend']['network_health'] == 'improving'
    assert any(event['type'] == 'redundancy_improved' for event in evolution['events'])



def test_compute_network_evolution_disables_trends_on_lineage_break(tmp_path: Path) -> None:
    registry_dir = tmp_path / 'analysis_runs'
    _register_bundle(tmp_path, registry_dir, run_name='run_001', analysis_version='2026.03', critical_station_count=1, redundancy_score=0.4, confidence_score=0.7)
    _register_bundle(tmp_path, registry_dir, run_name='run_002', analysis_version='2026.04', critical_station_count=0, redundancy_score=0.7, confidence_score=0.7)

    evolution = compute_network_evolution(registry_dir)

    assert evolution['lineage']['consistent'] is False
    assert evolution['lineage']['breakpoints'] == [
        {'run_id': 'run_002', 'reason': 'analysis_version_changed'}
    ]
    assert evolution['events'] == []
    assert evolution['trend'] == {
        'network_redundancy': 'unknown',
        'network_health': 'unknown',
    }
