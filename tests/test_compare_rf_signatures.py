from __future__ import annotations

import json
from pathlib import Path

from scripts.compare_rf_signatures import compare, latest_runs, load_rf_signature, metric_section, schema_diff, summarize_rows


def _write_run(run_dir: Path, rf_signature: dict, *, version: int | None = 2) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {'rf_signature': rf_signature}
    if version is not None:
        payload['rf_signature_version'] = version
    (run_dir / 'report.json').write_text(json.dumps(payload), encoding='utf-8')


def test_load_rf_signature_reads_report() -> None:
    run_dir = Path('tests/.tmp_compare_a')
    try:
        _write_run(run_dir, {'anisotropy_index': 4.5}, version=2)
        version, signature = load_rf_signature(run_dir)
        assert version == 2
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


def test_schema_diff_reports_added_and_removed_fields() -> None:
    added, removed = schema_diff(
        {'anisotropy_index': 4.4},
        {'anisotropy_index': 4.5, 'direction_entropy': 0.9},
    )
    assert added == ['direction_entropy']
    assert removed == []


def test_summarize_rows_reports_section_stability() -> None:
    rows = [
        ('direction', 'anisotropy_index', 4.4, 4.7, 0.3, '*'),
        ('distance', 'distance_spread_index', 0.6, 0.6, 0.0, ''),
        ('context', 'packet_count', 10, 11, 1.0, ''),
    ]
    summary = summarize_rows(rows)
    assert summary == {
        'direction': 'changed',
        'distance': 'stable',
        'context': 'stable',
    }


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
