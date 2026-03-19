from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .report_export import export_network_report_json


def export_network_report_json_file(
    contract: dict[str, Any],
    path: str | Path,
) -> Path:
    """Persist canonical contract JSON artifact to disk."""
    artifact = export_network_report_json(contract)

    target_path = Path(path)
    target_path.parent.mkdir(parents=True, exist_ok=True)

    with target_path.open('w', encoding='utf-8') as file_handle:
        json.dump(artifact, file_handle, indent=2, sort_keys=True)

    return target_path


__all__ = ['export_network_report_json_file']
