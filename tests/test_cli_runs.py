from __future__ import annotations

from pathlib import Path

import pandas as pd

from ogn_tool.cli_runs import main as runs_main
from ogn_tool.reporting.network_engineering_report import NetworkEngineeringReport
from ogn_tool.reporting.run_artifact_bundle import export_analysis_run_bundle
from ogn_tool.reporting.run_comparability import build_run_comparability
from ogn_tool.reporting.run_registry import register_run



def _build_report(*, critical_station_count: int, redundancy_score: float, confidence_score: float) -> NetworkEngineeringReport:
    rows = [
        {
            'station_id': f'S{index + 1}',
            'health_status': 'CRITICAL' if index < critical_station_count else 'GOOD',
        }
        for index in range(max(critical_station_count, 1))
    ]
    return NetworkEngineeringReport(
        network_summary={
            'network_status': 'WARNING' if critical_station_count else 'GOOD',
            'critical_station_count': critical_station_count,
            'warning_station_count': 0,
        },
        station_health_table=pd.DataFrame(rows),
        network_redundancy={'redundancy_score': redundancy_score, 'interpretation': 'x'},
        network_confidence={'confidence_score': confidence_score},
    )



def _register_bundle(tmp_path: Path, registry_dir: Path, run_name: str, *, critical_station_count: int, redundancy_score: float) -> Path:
    bundle_path = tmp_path / run_name
    export_analysis_run_bundle(
        _build_report(critical_station_count=critical_station_count, redundancy_score=redundancy_score, confidence_score=0.8),
        bundle_path,
        dataset_identity={
            'dataset_id': 'dataset-001',
            'packet_count': 123,
            'time_start': '2026-03-14T10:00:00Z',
            'time_end': '2026-03-14T11:00:00Z',
            'source': 'ogn_sqlite',
        },
        comparability=build_run_comparability(
            analysis_version='2026.03',
            time_window_start='2026-03-14T10:00:00Z',
            time_window_end='2026-03-14T11:00:00Z',
            config_identity='cfg_abc123',
        ),
    )
    register_run(bundle_path, registry_dir)
    return bundle_path



def test_runs_latest_command_outputs_latest_run(tmp_path: Path, capsys) -> None:
    registry_dir = tmp_path / 'analysis_runs'
    _register_bundle(tmp_path, registry_dir, 'run_001', critical_station_count=1, redundancy_score=0.4)

    exit_code = runs_main(['latest', str(registry_dir)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert 'Latest run' in captured.out
    assert 'run_001' in captured.out



def test_runs_compare_command_outputs_comparison(tmp_path: Path, capsys) -> None:
    left = _register_bundle(tmp_path, tmp_path / 'analysis_runs', 'run_001', critical_station_count=1, redundancy_score=0.4)
    right = _register_bundle(tmp_path, tmp_path / 'analysis_runs', 'run_002', critical_station_count=0, redundancy_score=0.7)

    exit_code = runs_main(['compare', str(left), str(right)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert 'Run comparison' in captured.out
    assert 'Redundancy delta:' in captured.out



def test_runs_evolution_command_outputs_trend(tmp_path: Path, capsys) -> None:
    registry_dir = tmp_path / 'analysis_runs'
    _register_bundle(tmp_path, registry_dir, 'run_001', critical_station_count=1, redundancy_score=0.4)
    _register_bundle(tmp_path, registry_dir, 'run_002', critical_station_count=0, redundancy_score=0.7)

    exit_code = runs_main(['evolution', str(registry_dir), '--last', '10'])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert 'Network evolution' in captured.out
    assert 'Redundancy trend:' in captured.out
