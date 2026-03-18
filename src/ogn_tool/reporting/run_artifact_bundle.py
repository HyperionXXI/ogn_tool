from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .network_engineering_report import NetworkEngineeringReport
from .report_export_io import export_network_report_json_file

BUNDLE_EXPORT_VERSION = '1.0'


def _try_write_ui_artifact(bundle_dir: Path) -> None:
    """Best-effort UI projection write; never fail bundle export."""
    try:
        from .ui_loader import write_ui_artifact

        write_ui_artifact(bundle_dir)
    except Exception:
        pass



def _write_additional_artifact(bundle_dir: Path, artifact_name: str, payload: Any) -> None:
    """Persist an additional JSON artifact inside the run bundle."""
    artifact_path = bundle_dir / f'{artifact_name}.json'
    with artifact_path.open('w', encoding='utf-8') as file_handle:
        json.dump(payload, file_handle, indent=2, sort_keys=True)



def export_analysis_run_bundle(
    report: NetworkEngineeringReport,
    output_dir: str | Path,
    *,
    run_metadata: dict[str, Any] | None = None,
    dataset_identity: dict[str, Any] | None = None,
    comparability: dict[str, Any] | None = None,
    additional_artifacts: dict[str, Any] | None = None,
) -> Path:
    """Export a reproducible artifact bundle for a single analysis run.

    Architectural rule:
    This module must consume report_export_io and must not access
    NetworkEngineeringReport internals directly.
    """
    bundle_dir = Path(output_dir)
    bundle_dir.mkdir(parents=True, exist_ok=True)

    export_network_report_json_file(report, bundle_dir / 'report.json')

    generated_at = (
        datetime.now(timezone.utc)
        .isoformat(timespec='seconds')
        .replace('+00:00', 'Z')
    )
    metadata_artifact = {
        'bundle_version': BUNDLE_EXPORT_VERSION,
        'generated_at': generated_at,
        'metadata': dict(run_metadata or {}),
        'dataset': dict(dataset_identity or {}),
    }
    if comparability is not None:
        metadata_artifact['comparability'] = dict(comparability)
    with (bundle_dir / 'run_metadata.json').open('w', encoding='utf-8') as file_handle:
        json.dump(metadata_artifact, file_handle, indent=2, sort_keys=True)

    # Product-layer artifact: stable UI projection of report + metadata.
    _try_write_ui_artifact(bundle_dir)

    for artifact_name, payload in (additional_artifacts or {}).items():
        _write_additional_artifact(bundle_dir, artifact_name, payload)

    return bundle_dir


__all__ = ['BUNDLE_EXPORT_VERSION', 'export_analysis_run_bundle']
