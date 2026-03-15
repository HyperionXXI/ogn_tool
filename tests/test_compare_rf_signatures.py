from __future__ import annotations

import json
from pathlib import Path

from scripts.compare_rf_signatures import compare, latest_runs, load_rf_signature, metric_section


def _write_run(run_dir: Path, rf_signature: dict) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / 'report.json').write_text(json.dumps({'rf_signature': rf_signature}), encoding='utf-8')


def test_load_rf_signature_reads_report() -> None:
    run_dir = Path('tests/.tmp_compare_a')
    try:
        _write_run(run_dir, {'anisotropy_index': 4.5})
        signature = load_rf_signature(run_dir)
        assert signature == {'anisotropy_index': 4.5}
    finally:
        if run_dir.exists():
            for child in run_dir.iterdir():
                child.unlink()
            run_dir.rmdir()


def test_compare_returns_grouped_rows_and_numeric_deltas() -> None:
    rows = compare(
        {'anisotropy_index': 4.4, 'corridor_center_deg': 105, 'packet_count': 10},
        {'anisotropy_index': 4.7, 'corridor_center_deg': 112, 'packet_count': 11},
    )
    assert ('direction', 'anisotropy_index', 4.4, 4.7, 0.2999999999999998, '*') in rows
    assert ('direction', 'corridor_center_deg', 105, 112, 7.0, '*') in rows
    assert ('context', 'packet_count', 10, 11, 1.0, '') in rows


def test_metric_section_defaults_to_other() -> None:
    assert metric_section('anisotropy_index') == 'direction'
    assert metric_section('distance_spread_index') == 'distance'
    assert metric_section('unknown_metric') == 'other'


def test_latest_runs_returns_most_recent_directories(tmp_path: Path) -> None:
    import time

    older = tmp_path / 'fk_old'
    newer = tmp_path / 'fk_new'
    _write_run(older, {'packet_count': 1})
    time.sleep(0.02)
    _write_run(newer, {'packet_count': 2})

    runs = latest_runs(tmp_path, n=2)
    assert runs[0].name == 'fk_new'
    assert runs[1].name == 'fk_old'
