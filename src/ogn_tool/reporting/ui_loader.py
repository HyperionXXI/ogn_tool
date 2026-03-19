from __future__ import annotations

from pathlib import Path
import json

from ogn_tool.reporting.views.dashboard_views import build_dashboard_payload


def load_json(path: Path) -> dict:
    with open(path, 'r', encoding='utf-8') as file_handle:
        data = json.load(file_handle)
    if not isinstance(data, dict):
        raise RuntimeError(f'invalid JSON object in {path}')
    return data


def build_ui_artifact_from_run(run_path: Path) -> dict:
    report_path = run_path / 'report.json'
    report = load_json(report_path)
    return build_dashboard_payload(report)


def write_ui_artifact(run_path: Path) -> Path:
    artifact = build_ui_artifact_from_run(run_path)
    out_path = run_path / 'ui_artifact.json'

    with open(out_path, 'w', encoding='utf-8') as file_handle:
        json.dump(artifact, file_handle, indent=2, sort_keys=True)

    return out_path
