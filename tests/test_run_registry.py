from __future__ import annotations

import json
from pathlib import Path

from ogn_tool.reporting.run_artifact_bundle import export_analysis_run_bundle
from ogn_tool.reporting.run_registry import list_runs, load_run_metadata, register_run
from ogn_tool.reporting.network_engineering_report import NetworkEngineeringReport



def test_list_runs_returns_empty_for_missing_registry(tmp_path: Path) -> None:
    assert list_runs(tmp_path / 'analysis_runs') == []



def test_register_run_creates_registry_index(tmp_path: Path) -> None:
    registry_dir = tmp_path / 'analysis_runs'
    bundle_path = tmp_path / 'run_2026_03_14_001'
    export_analysis_run_bundle(
        NetworkEngineeringReport(),
        bundle_path,
        run_metadata={'dataset': 'sample'},
    )

    register_run(bundle_path, registry_dir)

    index_path = registry_dir / 'index.json'
    assert index_path.exists()

    index_data = json.loads(index_path.read_text(encoding='utf-8'))
    assert 'runs' in index_data
    assert len(index_data['runs']) == 1
    assert index_data['runs'][0]['run_id'] == 'run_2026_03_14_001'
    assert index_data['runs'][0]['path'] == str(bundle_path)



def test_load_run_metadata_reads_bundle_metadata(tmp_path: Path) -> None:
    bundle_path = tmp_path / 'run_2026_03_14_001'
    export_analysis_run_bundle(
        NetworkEngineeringReport(),
        bundle_path,
        run_metadata={'dataset': 'sample', 'station_count': 4},
    )

    metadata = load_run_metadata(bundle_path)

    assert metadata['bundle_version'] == '1.0'
    assert metadata['metadata'] == {'dataset': 'sample', 'station_count': 4}



def test_list_runs_returns_registered_runs(tmp_path: Path) -> None:
    registry_dir = tmp_path / 'analysis_runs'
    bundle_path = tmp_path / 'run_2026_03_14_001'
    export_analysis_run_bundle(NetworkEngineeringReport(), bundle_path)
    register_run(bundle_path, registry_dir)

    runs = list_runs(registry_dir)

    assert len(runs) == 1
    assert runs[0]['run_id'] == 'run_2026_03_14_001'
