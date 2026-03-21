from __future__ import annotations

import json
from pathlib import Path

from ogn_tool.reporting.network_engineering_report import NetworkEngineeringReport
from ogn_tool.reporting.run_artifact_bundle import export_analysis_run_bundle


def test_export_analysis_run_bundle_creates_artifacts(tmp_path: Path) -> None:
    bundle_dir = tmp_path / 'run-001'
    report = NetworkEngineeringReport()

    result = export_analysis_run_bundle(
        report,
        bundle_dir,
        run_metadata={'label': 'sample-run', 'station_count': 4},
        dataset_identity={
            'dataset_id': 'dataset-001',
            'packet_count': 123,
            'time_start': '2026-03-14T10:00:00Z',
            'time_end': '2026-03-14T11:00:00Z',
            'source': 'ogn_sqlite',
        },
        comparability={
            'schema_version': '1.0',
            'analysis_version': '2026.03',
            'time_window_start': '2026-03-14T10:00:00Z',
            'time_window_end': '2026-03-14T11:00:00Z',
            'time_window_duration_s': 3600,
            'config_identity': 'cfg_abc123',
        },
        additional_artifacts={
            'azimuth_distance_surface': {
                'surface_type': 'azimuth_distance',
                'version': 1,
                'packet_count': 3,
            }
        },
    )

    assert result == bundle_dir
    assert result.exists()
    assert (result / 'report.json').exists()
    assert (result / 'run_metadata.json').exists()
    assert (result / 'azimuth_distance_surface.json').exists()

    report_json = json.loads((result / 'report.json').read_text(encoding='utf-8'))
    assert set(report_json.keys()) == {'run_id', 'metadata', 'network_metrics', 'coverage_score'}
    assert set(report_json['network_metrics'].keys()) == {
        'network_summary',
        'station_health',
        'station_dependency',
        'network_robustness',
        'station_placement',
    }
    assert 'report_metadata' not in report_json
    assert 'diagnostics' not in report_json

    metadata = json.loads((result / 'run_metadata.json').read_text(encoding='utf-8'))
    assert metadata['bundle_version'] == '1.0'
    assert 'generated_at' in metadata
    assert metadata['metadata'] == {'label': 'sample-run', 'station_count': 4}
    assert metadata['dataset'] == {
        'dataset_id': 'dataset-001',
        'packet_count': 123,
        'time_start': '2026-03-14T10:00:00Z',
        'time_end': '2026-03-14T11:00:00Z',
        'source': 'ogn_sqlite',
    }
    assert metadata['comparability'] == {
        'schema_version': '1.0',
        'analysis_version': '2026.03',
        'time_window_start': '2026-03-14T10:00:00Z',
        'time_window_end': '2026-03-14T11:00:00Z',
        'time_window_duration_s': 3600,
        'config_identity': 'cfg_abc123',
    }

    artifact = json.loads((result / 'azimuth_distance_surface.json').read_text(encoding='utf-8'))
    assert artifact == {
        'surface_type': 'azimuth_distance',
        'version': 1,
        'packet_count': 3,
    }


def test_export_analysis_run_bundle_without_comparability(tmp_path: Path) -> None:
    bundle_dir = tmp_path / 'run-002'
    result = export_analysis_run_bundle(NetworkEngineeringReport(), bundle_dir)

    metadata = json.loads((result / 'run_metadata.json').read_text(encoding='utf-8'))

    assert 'comparability' not in metadata
