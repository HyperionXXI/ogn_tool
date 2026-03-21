from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

if __package__ in (None, ''):
    repo_root = Path(__file__).resolve().parents[1]
    src_path = repo_root / 'src'
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

from ogn_tool.kernel.azimuth_distance_matrix import compute_azimuth_distance_matrix
from ogn_tool.domain.rf.dataset_identity import build_dataset_identity
from ogn_tool.domain.rf.rf_observations import compute_bearing, compute_distance
from ogn_tool.reporting import (
    build_azimuth_distance_summary,
    build_network_engineering_report,
    build_run_comparability,
    export_analysis_run_bundle,
)
from ogn_tool.reporting.run_registry import register_run
from ogn_tool.pipeline import rf_analysis_service

DEFAULT_DB_PATH = r"F:\Data\ogn\ogn_log.sqlite3"
DEFAULT_RUNS_DIR = Path('data/runs/analysis_runs')
DEFAULT_STATIONS_CONFIG = Path('docs/validation/stations_multisite.json')
DEFAULT_WINDOW_HOURS = 6
LIMIT_ROWS = 100000
ANALYSIS_VERSION = '2026.03'
CONFIG_IDENTITY = 'multistation_window_v1'
AZIMUTH_BINS = [float(value) for value in range(0, 361, 10)]
DISTANCE_BINS_KM = [float(value) for value in range(0, 151, 10)]


@dataclass
class StationSpec:
    station_id: str
    lat: float
    lon: float


def _build_azimuth_distance_surface(packets, station_lat: float, station_lon: float) -> dict[str, Any]:
    observations = packets.copy()
    observations['distance_km'] = compute_distance(observations, station_lat, station_lon)
    observations['bearing_deg'] = compute_bearing(observations, station_lat, station_lon)

    surface = compute_azimuth_distance_matrix(
        observations,
        AZIMUTH_BINS,
        DISTANCE_BINS_KM,
    )
    summary = build_azimuth_distance_summary(surface)
    return {
        'surface_type': 'azimuth_distance',
        'version': 1,
        **surface,
        'summary': summary,
    }


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except Exception:
        return None


def _load_station_specs(config_path: Path, selected_ids: set[str] | None) -> list[StationSpec]:
    if not config_path.exists():
        raise SystemExit(f'stations config not found: {config_path}')

    try:
        payload = json.loads(config_path.read_text(encoding='utf-8'))
    except Exception as exc:
        raise SystemExit(f'invalid JSON in {config_path}: {exc}')

    stations = payload.get('stations') if isinstance(payload, dict) else None
    if not isinstance(stations, list):
        raise SystemExit(f'invalid stations list in {config_path}')

    specs: list[StationSpec] = []
    for row in stations:
        if not isinstance(row, dict):
            continue
        station_id = str(row.get('station_id') or '').strip().upper()
        lat = _safe_float(row.get('lat'))
        lon = _safe_float(row.get('lon'))
        if not station_id or lat is None or lon is None:
            continue
        if selected_ids and station_id not in selected_ids:
            continue
        specs.append(StationSpec(station_id=station_id, lat=lat, lon=lon))

    if not specs:
        raise SystemExit('no stations selected from config')

    return specs


def _parse_selected_stations(raw: str | None) -> set[str] | None:
    if not raw:
        return None
    selected = {item.strip().upper() for item in raw.split(',') if item.strip()}
    return selected or None


def _format_utc(dt: datetime) -> str:
    return dt.isoformat(timespec='seconds').replace('+00:00', 'Z')


def _build_run_id(station_id: str, end_dt: datetime, window_hours: int, end_offset_hours: int) -> str:
    prefix = station_id.lower()
    return end_dt.strftime(f'{prefix}_%Y_%m_%d_%H%M%S_{window_hours}h_offset{end_offset_hours}h')


def main() -> None:
    parser = argparse.ArgumentParser(description='Run synchronized multi-station analysis window')
    parser.add_argument('--stations-config', default=str(DEFAULT_STATIONS_CONFIG))
    parser.add_argument('--stations', help='Comma-separated station IDs to run (subset of config)')
    parser.add_argument('--window-hours', type=int, default=DEFAULT_WINDOW_HOURS)
    parser.add_argument('--end-offset-hours', type=int, default=0)
    parser.add_argument('--db-path', default=DEFAULT_DB_PATH)
    parser.add_argument('--runs-dir', default=str(DEFAULT_RUNS_DIR))
    parser.add_argument('--limit-rows', type=int, default=LIMIT_ROWS)
    args = parser.parse_args()

    selected_ids = _parse_selected_stations(args.stations)
    specs = _load_station_specs(Path(args.stations_config), selected_ids)

    max_ts = rf_analysis_service.db_max_ts_epoch(args.db_path)
    if not max_ts:
        raise SystemExit('No timestamp found in database.')

    # Compute one shared time window and reuse it for every station.
    end_dt = datetime.fromtimestamp(int(max_ts), tz=timezone.utc) - timedelta(hours=args.end_offset_hours)
    start_dt = end_dt - timedelta(hours=args.window_hours)
    time_start = _format_utc(start_dt)
    time_end = _format_utc(end_dt)

    registry_dir = Path(args.runs_dir)
    registry_dir.mkdir(parents=True, exist_ok=True)

    print(f'Window start: {time_start}')
    print(f'Window end:   {time_end}')
    print(f'Stations: {", ".join(spec.station_id for spec in specs)}')
    print('---')

    for spec in specs:
        try:
            packets = rf_analysis_service.load_rf_receptions(
                db_path=args.db_path,
                since_epoch=int(start_dt.timestamp()),
                end_epoch=int(end_dt.timestamp()),
                limit_rows=int(args.limit_rows),
                station_id=spec.station_id,
            )
        except Exception as exc:
            print(f'{spec.station_id}: ERROR load_rf_receptions ({exc})')
            continue

        packet_count = 0 if packets is None else int(len(packets))
        if packets is None or packets.empty:
            print(f'{spec.station_id}: SKIP no receptions')
            continue

        rf_analysis_service.build_rf_dataset(
            packets_df=packets,
            station_lat=spec.lat,
            station_lon=spec.lon,
            dataset_mode='NETWORK',
            station_id=spec.station_id,
        )

        station_analysis = rf_analysis_service.run_station_analysis(
            dataset_mode='NETWORK',
            station_id=spec.station_id,
        )
        network_analysis = rf_analysis_service.run_network_analysis(
            dataset_mode='NETWORK',
            station_id=spec.station_id,
        )

        report = build_network_engineering_report(
            network_analysis.get('network_metrics') if isinstance(network_analysis, dict) else {},
            network_analysis.get('spatial_observations') if isinstance(network_analysis, dict) else None,
        )
        azimuth_distance_surface = _build_azimuth_distance_surface(packets, spec.lat, spec.lon)
        report.rf_signature = dict(azimuth_distance_surface.get('summary', {}).get('rf_signature') or {})

        dataset_identity = build_dataset_identity(
            packet_count=packet_count,
            time_start=time_start,
            time_end=time_end,
            source='ogn_sqlite',
        )
        comparability = build_run_comparability(
            analysis_version=ANALYSIS_VERSION,
            time_window_start=time_start,
            time_window_end=time_end,
            config_identity=CONFIG_IDENTITY,
        )

        lag_hours = int((datetime.now(timezone.utc) - end_dt).total_seconds() // 3600)

        run_id = _build_run_id(spec.station_id, end_dt, args.window_hours, args.end_offset_hours)
        bundle_dir = registry_dir / run_id

        export_analysis_run_bundle(
            report,
            bundle_dir,
            run_metadata={
                'station_id': spec.station_id,
                'analysis_scope': 'station_signature',
                'window_hours': int(args.window_hours),
                'end_offset_hours': int(args.end_offset_hours),
                'db_path': str(args.db_path),
                'data_freshness_lag_hours': lag_hours,
                'station_lat': spec.lat,
                'station_lon': spec.lon,
            },
            dataset_identity=dataset_identity,
            comparability=comparability,
            additional_artifacts={
                'azimuth_distance_surface': azimuth_distance_surface,
            },
        )
        register_run(bundle_dir, registry_dir)

        print(
            f"{spec.station_id}: OK run_id={run_id} packets={packet_count} "
            f"az_packets={azimuth_distance_surface.get('packet_count')} "
            f"station_keys={list((station_analysis or {}).keys())}"
        )


if __name__ == '__main__':
    main()
