from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


DEFAULT_RUNS_DIR = Path("analysis_runs")
SECTION_ORDER = {
    'anisotropy_index': 'direction',
    'direction_entropy': 'direction',
    'dominant_corridor_start_deg': 'direction',
    'dominant_corridor_end_deg': 'direction',
    'corridor_center_deg': 'direction',
    'corridor_width_deg': 'direction',
    'dominant_corridor_share': 'direction',
    'dominant_distance_band_km': 'distance',
    'dominant_distance_band_share': 'distance',
    'nonzero_distance_band_count': 'distance',
    'distance_spread_index': 'distance',
    'packet_count': 'context',
    'interpretation': 'context',
}
SECTION_SORT = {'direction': 0, 'distance': 1, 'context': 2, 'other': 3}
DELTA_THRESHOLDS = {
    'anisotropy_index': 0.2,
    'direction_entropy': 0.02,
    'dominant_corridor_share': 0.02,
    'dominant_distance_band_share': 0.05,
    'distance_spread_index': 0.05,
    'corridor_center_deg': 5.0,
    'corridor_width_deg': 10.0,
}


def load_report(run_path: str | Path) -> dict[str, Any]:
    report_path = Path(run_path) / 'report.json'
    if not report_path.exists():
        raise SystemExit(f'report.json not found in {run_path}')

    with report_path.open('r', encoding='utf-8') as file_handle:
        report = json.load(file_handle)
    if not isinstance(report, dict):
        raise SystemExit(f'invalid report.json in {run_path}')
    return report


def load_rf_signature(run_path: str | Path) -> tuple[int | None, dict[str, Any]]:
    report = load_report(run_path)
    version = report.get('rf_signature_version')
    if version is not None and not isinstance(version, int):
        raise SystemExit(f'rf_signature_version invalid in {run_path}')

    signature = report.get('rf_signature', {})
    if not isinstance(signature, dict):
        raise SystemExit(f'rf_signature missing or invalid in {run_path}')
    return version, signature


def latest_runs(base: str | Path = DEFAULT_RUNS_DIR, n: int = 2) -> list[Path]:
    runs = sorted(
        Path(base).glob('fk*'),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    directories = [path for path in runs if path.is_dir()]
    if len(directories) < n:
        raise SystemExit(f'Expected at least {n} run directories in {base}')
    return directories[:n]


def fmt(value: Any) -> str:
    if isinstance(value, float):
        return f'{value:.4f}'
    if isinstance(value, list):
        return '[' + ', '.join(fmt(item) for item in value) + ']'
    if value is None:
        return ''
    return str(value)


def metric_section(metric: str) -> str:
    return SECTION_ORDER.get(metric, 'other')


def metric_sort_key(metric: str) -> tuple[int, str]:
    section = metric_section(metric)
    return (SECTION_SORT.get(section, SECTION_SORT['other']), metric)


def delta_marker(metric: str, delta: float | None) -> str:
    if delta is None:
        return ''
    threshold = DELTA_THRESHOLDS.get(metric)
    if threshold is None:
        return ''
    return '*' if abs(delta) > threshold else ''


def compare(sig_a: dict[str, Any], sig_b: dict[str, Any]) -> list[tuple[str, str, Any, Any, float | None, str]]:
    keys = sorted(set(sig_a) | set(sig_b), key=metric_sort_key)

    rows: list[tuple[str, str, Any, Any, float | None, str]] = []
    for key in keys:
        value_a = sig_a.get(key)
        value_b = sig_b.get(key)

        delta = None
        if isinstance(value_a, (int, float)) and isinstance(value_b, (int, float)):
            delta = float(value_b - value_a)

        rows.append((metric_section(key), key, value_a, value_b, delta, delta_marker(key, delta)))

    return rows


def schema_diff(sig_a: dict[str, Any], sig_b: dict[str, Any]) -> tuple[list[str], list[str]]:
    keys_a = set(sig_a)
    keys_b = set(sig_b)
    added = sorted(keys_b - keys_a, key=metric_sort_key)
    removed = sorted(keys_a - keys_b, key=metric_sort_key)
    return added, removed


def print_schema_info(version_a: int | None, version_b: int | None, added: list[str], removed: list[str]) -> None:
    print('Signature schema:')
    print(f'  runA version: {version_a if version_a is not None else "unknown"}')
    print(f'  runB version: {version_b if version_b is not None else "unknown"}')
    if version_a != version_b:
        print('  warning: rf_signature_version mismatch')
    print(f'  added fields: {", ".join(added) if added else "none"}')
    print(f'  removed fields: {", ".join(removed) if removed else "none"}')


def print_table(rows: list[tuple[str, str, Any, Any, float | None, str]], run_a_label: str, run_b_label: str) -> None:
    current_section = None
    for section, key, value_a, value_b, delta, marker in rows:
        if section != current_section:
            current_section = section
            print(f'\n[{section}]')
            print(f"{'metric':30} {run_a_label:15} {run_b_label:15} {'delta':15} {'flag':4}")
            print('-' * 90)

        delta_str = ''
        if isinstance(delta, float):
            delta_str = f'{delta:+.4f}'

        print(
            f'{key:30} '
            f'{fmt(value_a):15} '
            f'{fmt(value_b):15} '
            f'{delta_str:15} '
            f'{marker:4}'
        )


def summarize_rows(rows: list[tuple[str, str, Any, Any, float | None, str]]) -> dict[str, str]:
    summary: dict[str, str] = {}
    sections = sorted({section for section, *_ in rows}, key=lambda section: SECTION_SORT.get(section, SECTION_SORT['other']))
    for section in sections:
        section_rows = [row for row in rows if row[0] == section]
        changed = any(marker == '*' for _, _, _, _, _, marker in section_rows)
        summary[section] = 'changed' if changed else 'stable'
    return summary


def print_summary(summary: dict[str, str]) -> None:
    print('\nRF signature comparison summary')
    print('-----------------------------')
    for section in ['direction', 'distance', 'context', 'other']:
        if section in summary:
            print(f'{section}: {summary[section]}')

    structural_sections = [summary.get('direction'), summary.get('distance')]
    if all(value == 'stable' for value in structural_sections if value is not None):
        print('overall: no structural changes detected')
    else:
        print('overall: structural changes detected')


def main() -> None:
    parser = argparse.ArgumentParser(description='Compare rf_signature between two analysis runs')
    parser.add_argument('run_a', help="First run directory or 'latest'")
    parser.add_argument('run_b', nargs='?', help="Second run directory when run_a is not 'latest'")
    parser.add_argument('--runs-dir', default=str(DEFAULT_RUNS_DIR), help='Base directory containing run bundles')
    args = parser.parse_args()

    if args.run_a == 'latest':
        if args.run_b is not None:
            raise SystemExit("Do not pass run_b when using 'latest'.")
        run_b_path, run_a_path = latest_runs(args.runs_dir, n=2)
    else:
        if args.run_b is None:
            raise SystemExit('Usage: compare_rf_signatures.py runA runB | compare_rf_signatures.py latest')
        run_a_path = Path(args.run_a)
        run_b_path = Path(args.run_b)

    version_a, sig_a = load_rf_signature(run_a_path)
    version_b, sig_b = load_rf_signature(run_b_path)

    added, removed = schema_diff(sig_a, sig_b)
    print_schema_info(version_a, version_b, added, removed)

    rows = compare(sig_a, sig_b)
    print_table(rows, Path(run_a_path).name, Path(run_b_path).name)
    print_summary(summarize_rows(rows))


if __name__ == '__main__':
    main()
