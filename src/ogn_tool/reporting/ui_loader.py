from __future__ import annotations

from pathlib import Path
import json

from ogn_tool.reporting.report_normalizer import build_ui_artifact


def load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data if isinstance(data, dict) else {}


def build_ui_artifact_from_run(run_path: Path) -> dict:
    report_path = run_path / "report.json"
    metadata_path = run_path / "run_metadata.json"

    report = load_json(report_path)
    metadata = load_json(metadata_path)

    return build_ui_artifact(report, metadata)


def write_ui_artifact(run_path: Path) -> Path:
    artifact = build_ui_artifact_from_run(run_path)

    out_path = run_path / "ui_artifact.json"

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2, sort_keys=True)

    return out_path

