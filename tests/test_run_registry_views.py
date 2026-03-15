from __future__ import annotations

from pathlib import Path

from ogn_tool.reporting.network_engineering_report import NetworkEngineeringReport
from ogn_tool.reporting.run_artifact_bundle import export_analysis_run_bundle
from ogn_tool.reporting.run_registry import register_run
from ogn_tool.reporting.run_registry_views import (
    get_latest_run,
    get_registered_runs,
    get_run_registry_summary,
)



def test_run_registry_views_handle_empty_registry(tmp_path: Path) -> None:
    registry_dir = tmp_path / 'analysis_runs'

    assert get_registered_runs(registry_dir) == []
    assert get_latest_run(registry_dir) is None
    assert get_run_registry_summary(registry_dir) == {
        'run_count': 0,
        'latest_run': None,
        'oldest_run': None,
    }



def test_run_registry_views_sort_and_summarize_runs(tmp_path: Path) -> None:
    registry_dir = tmp_path / 'analysis_runs'

    first_bundle = tmp_path / 'run_2026_03_14_001'
    export_analysis_run_bundle(
        NetworkEngineeringReport(),
        first_bundle,
        run_metadata={'label': 'first'},
    )
    register_run(first_bundle, registry_dir)

    second_bundle = tmp_path / 'run_2026_03_14_002'
    export_analysis_run_bundle(
        NetworkEngineeringReport(),
        second_bundle,
        run_metadata={'label': 'second'},
    )
    register_run(second_bundle, registry_dir)

    runs = get_registered_runs(registry_dir)
    latest = get_latest_run(registry_dir)
    summary = get_run_registry_summary(registry_dir)

    assert len(runs) == 2
    assert runs[0]['run_id'] == 'run_2026_03_14_002'
    assert runs[1]['run_id'] == 'run_2026_03_14_001'
    assert latest == runs[0]
    assert summary['run_count'] == 2
    assert summary['latest_run'] == runs[0]
    assert summary['oldest_run'] == runs[-1]
