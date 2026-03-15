from __future__ import annotations

from pathlib import Path

from .run_registry import list_runs



def _sorted_runs(registry_dir: Path) -> list[dict]:
    runs = [dict(run) for run in list_runs(Path(registry_dir))]
    runs.sort(
        key=lambda run: (
            str(run.get('generated_at') or ''),
            str(run.get('run_id') or ''),
        ),
        reverse=True,
    )
    return runs



def get_registered_runs(registry_dir: Path) -> list[dict]:
    """Return the registered runs ordered from most recent to oldest."""
    return _sorted_runs(Path(registry_dir))



def get_latest_run(registry_dir: Path) -> dict | None:
    """Return the most recent registered run, if any."""
    runs = get_registered_runs(Path(registry_dir))
    return runs[0] if runs else None



def get_run_registry_summary(registry_dir: Path) -> dict:
    """Return a stable summary projection of the run registry."""
    runs = get_registered_runs(Path(registry_dir))
    if not runs:
        return {
            'run_count': 0,
            'latest_run': None,
            'oldest_run': None,
        }

    return {
        'run_count': len(runs),
        'latest_run': runs[0],
        'oldest_run': runs[-1],
    }


__all__ = ['get_registered_runs', 'get_latest_run', 'get_run_registry_summary']
