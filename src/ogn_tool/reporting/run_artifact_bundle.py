from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .network_engineering_report import NetworkEngineeringReport
from .report_export_io import export_network_report_json_file

BUNDLE_EXPORT_VERSION = '1.0'



def export_analysis_run_bundle(
    report: NetworkEngineeringReport,
    output_dir: str | Path,
    *,
    run_metadata: dict[str, Any] | None = None,
    dataset_identity: dict[str, Any] | None = None,
    comparability: dict[str, Any] | None = None,
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

    return bundle_dir


__all__ = ['BUNDLE_EXPORT_VERSION', 'export_analysis_run_bundle']
