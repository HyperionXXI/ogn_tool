from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ''):
    repo_root = Path(__file__).resolve().parents[1]
    src_path = repo_root / 'src'
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

from ogn_tool.reporting.views.dashboard_views import build_dashboard_payload, load_report_from_path

DEFAULT_RUNS_DIR = Path('data/runs/analysis_runs')


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _resolve_run_dir(arg: str, runs_dir: Path) -> Path:
    candidate = Path(arg)
    if candidate.exists() and candidate.is_dir():
        return candidate

    nested = runs_dir / arg
    if nested.exists() and nested.is_dir():
        return nested

    raise SystemExit(f'Run directory not found: {arg}')


def load_rf_metrics(run_dir: Path) -> dict[str, Any]:
    report_path = run_dir / 'report.json'
    if not report_path.exists():
        raise SystemExit(f'report.json not found in {run_dir}')

    report = load_report_from_path(str(report_path))
    if report is None:
        report = json.loads(report_path.read_text(encoding='utf-8'))

    payload = build_dashboard_payload(report)
    rf = payload.get('intelligence', {}).get('rf_analysis', {}) if isinstance(payload, dict) else {}
    sig = rf.get('rf_signature', {}) if isinstance(rf, dict) else {}
    gap = rf.get('rf_gap_structure', {}) if isinstance(rf, dict) else {}

    run_id = report.get('run_id') if isinstance(report, dict) else run_dir.name
    if not isinstance(run_id, str) or not run_id:
        run_id = run_dir.name

    return {
        'run_id': run_id,
        'center': _safe_float(sig.get('corridor_center_deg')),
        'share': _safe_float(sig.get('dominant_corridor_share')),
        'uniformity': _safe_float(sig.get('coverage_uniformity_score')),
        'largest_gap': _safe_float(gap.get('largest_gap')),
    }


def is_stable(ref: dict[str, Any], current: dict[str, Any]) -> bool:
    keys = ('center', 'share', 'uniformity', 'largest_gap')
    if any(ref.get(k) is None or current.get(k) is None for k in keys):
        return False

    def close(a: float, b: float, tol: float) -> bool:
        return abs(a - b) <= tol

    return (
        close(float(current['center']), float(ref['center']), 10.0)
        and close(float(current['share']), float(ref['share']), 0.05)
        and close(float(current['uniformity']), float(ref['uniformity']), 0.05)
        and close(float(current['largest_gap']), float(ref['largest_gap']), 30.0)
    )


def _fmt_num(value: float | None, fmt: str) -> str:
    if value is None:
        return 'n/a'
    return format(value, fmt)


def main() -> None:
    parser = argparse.ArgumentParser(description='Build a RF stability comparison table across runs')
    parser.add_argument('runs', nargs='+', help='Run directories or run IDs')
    parser.add_argument('--runs-dir', default=str(DEFAULT_RUNS_DIR), help='Base directory containing run bundles')
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    run_dirs = [_resolve_run_dir(arg, runs_dir) for arg in args.runs]
    rows = [load_rf_metrics(run_dir) for run_dir in run_dirs]

    ref = rows[0]

    print(f"{'run_id':<40} {'center':>7} {'share':>7} {'uniformity':>10} {'largest_gap':>11} {'stable?':>8}")
    print('-' * 92)

    for row in rows:
        stable = 'YES' if is_stable(ref, row) else 'NO'
        center = _fmt_num(row['center'], '.0f')
        share = _fmt_num(row['share'], '.2f')
        uniformity = _fmt_num(row['uniformity'], '.2f')
        largest_gap = _fmt_num(row['largest_gap'], '.0f')

        if center != 'n/a':
            center = f'{center}°'

        print(
            f"{row['run_id']:<40} {center:>7} {share:>7} {uniformity:>10} {largest_gap:>11} {stable:>8}"
        )


if __name__ == '__main__':
    main()
