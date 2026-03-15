from __future__ import annotations

import json
from pathlib import Path



def load_run_metadata(bundle_path: Path) -> dict:
    """Load the stable metadata artifact for a single analysis run bundle."""
    metadata_path = Path(bundle_path) / 'run_metadata.json'
    with metadata_path.open('r', encoding='utf-8') as file_handle:
        data = json.load(file_handle)
    return data if isinstance(data, dict) else {}



def list_runs(registry_dir: Path) -> list[dict]:
    """Return the registered analysis runs from the registry index."""
    index_path = Path(registry_dir) / 'index.json'
    if not index_path.exists():
        return []

    with index_path.open('r', encoding='utf-8') as file_handle:
        data = json.load(file_handle)

    runs = data.get('runs', []) if isinstance(data, dict) else []
    return [run for run in runs if isinstance(run, dict)]



def register_run(bundle_path: Path, registry_dir: Path) -> None:
    """Register an analysis run bundle in the registry index."""
    bundle_path = Path(bundle_path)
    registry_dir = Path(registry_dir)
    registry_dir.mkdir(parents=True, exist_ok=True)

    metadata = load_run_metadata(bundle_path)
    runs = list_runs(registry_dir)

    run_entry = {
        'run_id': bundle_path.name,
        'path': str(bundle_path),
        'generated_at': metadata.get('generated_at'),
        'bundle_version': metadata.get('bundle_version'),
    }

    runs = [run for run in runs if run.get('run_id') != run_entry['run_id']]
    runs.append(run_entry)
    runs.sort(key=lambda run: (str(run.get('generated_at') or ''), str(run.get('run_id') or '')))

    index_path = registry_dir / 'index.json'
    with index_path.open('w', encoding='utf-8') as file_handle:
        json.dump({'runs': runs}, file_handle, indent=2, sort_keys=True)


__all__ = ['register_run', 'list_runs', 'load_run_metadata']
