from __future__ import annotations

import json
from pathlib import Path

from .network_engineering_report import NetworkEngineeringReport
from .report_export import export_network_report_json



def export_network_report_json_file(
    report: NetworkEngineeringReport,
    path: str | Path,
) -> Path:
    """Persist a stable JSON artifact to disk.

    Architectural rule:
    This module must consume export_network_report_json(...) and must
    not access NetworkEngineeringReport internals directly.
    """
    artifact = export_network_report_json(report)

    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with target_path.open('w', encoding='utf-8') as file_handle:
        json.dump(artifact, file_handle, indent=2, sort_keys=True)

    return target_path


__all__ = ['export_network_report_json_file']
