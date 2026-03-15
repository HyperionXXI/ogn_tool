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
    )

    assert result == bundle_dir
    assert result.exists()
    assert (result / 'report.json').exists()
    assert (result / 'run_metadata.json').exists()

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
