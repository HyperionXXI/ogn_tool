from pathlib import Path
import json

from ogn_tool.reporting.network_engineering_report import NetworkEngineeringReport
from ogn_tool.reporting.run_artifact_bundle import export_analysis_run_bundle
from ogn_tool.reporting.ui_loader import build_ui_artifact_from_run, write_ui_artifact


def test_build_ui_artifact_from_run_reads_files(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-001"
    run_dir.mkdir(parents=True, exist_ok=True)

    (run_dir / "report.json").write_text(json.dumps({"input_warnings": []}), encoding="utf-8")
    (run_dir / "run_metadata.json").write_text(json.dumps({"dataset": {"station_id": "S1"}}), encoding="utf-8")

    artifact = build_ui_artifact_from_run(run_dir)
    assert isinstance(artifact, dict)
    assert "meta" in artifact
    assert "layers" in artifact
    assert "network" in artifact
    assert "diagnostics" in artifact


def test_write_ui_artifact_creates_file(tmp_path: Path) -> None:
    run_dir = tmp_path / "run-002"
    run_dir.mkdir(parents=True, exist_ok=True)

    (run_dir / "report.json").write_text(json.dumps({"input_warnings": []}), encoding="utf-8")
    (run_dir / "run_metadata.json").write_text(json.dumps({"dataset": {"station_id": "S1"}}), encoding="utf-8")

    out_path = write_ui_artifact(run_dir)
    assert out_path.exists()
    assert out_path.name == "ui_artifact.json"


def test_export_analysis_run_bundle_writes_ui_artifact(tmp_path: Path) -> None:
    report = NetworkEngineeringReport(network_summary={}, input_warnings=[])
    out_dir = tmp_path / "bundle"

    bundle_dir = export_analysis_run_bundle(
        report,
        out_dir,
        dataset_identity={"station_id": "S1"},
        comparability={"time_window_start": None, "time_window_end": None, "time_window_duration_s": None, "analysis_version": "x", "config_identity": "y"},
    )

    assert (bundle_dir / "report.json").exists()
    assert (bundle_dir / "run_metadata.json").exists()
    assert (bundle_dir / "ui_artifact.json").exists()

