from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import sys

if __package__ in (None, ''):
    repo_root = Path(__file__).resolve().parents[1]
    src_path = repo_root / 'src'
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

from ogn_tool.pipeline.rf_analysis_service import load_rf_receptions

DEFAULT_RUNS_DIR = Path('data/runs/analysis_runs')
AIRCRAFT_COLUMN_CANDIDATES = (
    'addr',
    'address',
    'aircraft_id',
    'src',
    'src_call',
    'id',
)


@dataclass
class RunQuality:
    run_id: str
    packet_count: int
    unique_aircraft: int
    temporal_coverage_ratio: float
    is_valid: bool
    score: float
    reason: str = ''


def _parse_iso_utc(value: str | None) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    text = value.replace('Z', '+00:00')
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _pick_aircraft_column(columns: list[str]) -> str | None:
    lower_map = {col.lower(): col for col in columns}
    for candidate in AIRCRAFT_COLUMN_CANDIDATES:
        if candidate in lower_map:
            return lower_map[candidate]
    return None


def _compute_temporal_coverage_ratio(ts_values, window_seconds: int, bucket_seconds: int = 3600) -> float:
    if window_seconds <= 0:
        return 0.0
    if ts_values is None:
        return 0.0
    try:
        cleaned = [int(value) for value in ts_values if value is not None]
    except Exception:
        return 0.0
    if not cleaned:
        return 0.0

    buckets = {value // bucket_seconds for value in cleaned}
    expected = max(1, math.ceil(window_seconds / bucket_seconds))
    ratio = len(buckets) / expected
    return max(0.0, min(1.0, float(ratio)))


def evaluate_run(
    run_dir: Path,
    min_packet_count: int,
    min_unique_aircraft: int,
    min_temporal_coverage_ratio: float,
) -> RunQuality:
    run_id = run_dir.name
    run_metadata = _read_json(run_dir / 'run_metadata.json')
    dataset = run_metadata.get('dataset') if isinstance(run_metadata.get('dataset'), dict) else {}
    comparability = run_metadata.get('comparability') if isinstance(run_metadata.get('comparability'), dict) else {}
    metadata = run_metadata.get('metadata') if isinstance(run_metadata.get('metadata'), dict) else {}

    packet_count = int(dataset.get('packet_count') or 0)
    db_path = metadata.get('db_path')
    station_id = metadata.get('station_id')

    window_start = _parse_iso_utc(comparability.get('time_window_start'))
    window_end = _parse_iso_utc(comparability.get('time_window_end'))
    duration_s = int(comparability.get('time_window_duration_s') or 0)
    if duration_s <= 0 and window_start and window_end:
        duration_s = max(0, int((window_end - window_start).total_seconds()))

    if not db_path or not window_start or not window_end:
        return RunQuality(
            run_id=run_id,
            packet_count=packet_count,
            unique_aircraft=0,
            temporal_coverage_ratio=0.0,
            is_valid=False,
            score=0.0,
            reason='missing_db_or_window_metadata',
        )

    try:
        receptions = load_rf_receptions(
            db_path=str(db_path),
            since_epoch=int(window_start.timestamp()),
            end_epoch=int(window_end.timestamp()),
            limit_rows=max(packet_count * 2, 10000),
            station_id=str(station_id) if station_id else None,
        )
    except Exception:
        return RunQuality(
            run_id=run_id,
            packet_count=packet_count,
            unique_aircraft=0,
            temporal_coverage_ratio=0.0,
            is_valid=False,
            score=0.0,
            reason='db_query_failed',
        )

    if receptions is None or receptions.empty:
        return RunQuality(
            run_id=run_id,
            packet_count=packet_count,
            unique_aircraft=0,
            temporal_coverage_ratio=0.0,
            is_valid=False,
            score=0.0,
            reason='no_receptions',
        )

    aircraft_col = _pick_aircraft_column(list(receptions.columns))
    unique_aircraft = int(receptions[aircraft_col].astype(str).nunique()) if aircraft_col else 0

    temporal_coverage_ratio = 0.0
    if 'ts_epoch' in receptions.columns:
        temporal_coverage_ratio = _compute_temporal_coverage_ratio(receptions['ts_epoch'].tolist(), duration_s)

    is_valid = (
        packet_count >= min_packet_count
        and unique_aircraft >= min_unique_aircraft
        and temporal_coverage_ratio >= min_temporal_coverage_ratio
    )
    score = float(packet_count * temporal_coverage_ratio * math.log(1 + max(unique_aircraft, 0)))

    return RunQuality(
        run_id=run_id,
        packet_count=packet_count,
        unique_aircraft=unique_aircraft,
        temporal_coverage_ratio=temporal_coverage_ratio,
        is_valid=is_valid,
        score=score,
    )


def _list_run_dirs(runs_dir: Path) -> list[Path]:
    if not runs_dir.exists():
        return []
    return sorted([path for path in runs_dir.iterdir() if path.is_dir()], key=lambda path: path.stat().st_mtime, reverse=True)


def _print_table(rows: list[RunQuality], top: int) -> None:
    print(f"{'run_id':40} {'valid':5} {'score':10} {'packet':8} {'aircraft':8} {'tcr':6} reason")
    print('-' * 100)
    for item in rows[:top]:
        valid = 'YES' if item.is_valid else 'NO'
        print(
            f"{item.run_id:40} {valid:5} {item.score:10.0f} {item.packet_count:8d} "
            f"{item.unique_aircraft:8d} {item.temporal_coverage_ratio:6.2f} {item.reason}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description='Run quality gate for RF runs')
    parser.add_argument('--runs-dir', default=str(DEFAULT_RUNS_DIR), help='Run bundles directory')
    parser.add_argument('--min-packet-count', type=int, default=500)
    parser.add_argument('--min-unique-aircraft', type=int, default=10)
    parser.add_argument('--min-temporal-coverage-ratio', type=float, default=0.5)
    parser.add_argument('--top', type=int, default=20, help='Rows to display')
    parser.add_argument('--valid-only', action='store_true', help='Only display valid runs')
    args = parser.parse_args()

    runs_dir = Path(args.runs_dir)
    runs = _list_run_dirs(runs_dir)
    results = [
        evaluate_run(
            run_dir,
            min_packet_count=args.min_packet_count,
            min_unique_aircraft=args.min_unique_aircraft,
            min_temporal_coverage_ratio=args.min_temporal_coverage_ratio,
        )
        for run_dir in runs
    ]
    results.sort(key=lambda item: item.score, reverse=True)

    if args.valid_only:
        results = [item for item in results if item.is_valid]

    _print_table(results, top=args.top)

    total = len(results)
    valid_count = sum(1 for item in results if item.is_valid)
    print()
    print('Summary')
    print('-------')
    print(f'total_runs: {total}')
    print(f'valid_runs: {valid_count}')


if __name__ == '__main__':
    main()
