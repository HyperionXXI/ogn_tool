from __future__ import annotations

import json
import logging
import os
import socket
import sqlite3
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from fastapi.staticfiles import StaticFiles

from ogn_tool.domain.aircraft_observations import (
    build_aircraft_observations,
    project_aircraft_positions,
)
from ogn_tool.reporting.views.dashboard_views import build_dashboard_payload, load_report_from_path
from ogn_tool.kernel.rf_exploration import (
    get_blind_zones,
    get_diagnosis,
    get_directional,
    get_rf_field,
    get_rf_quality,
    get_timeseries,
    get_visibility,
    get_messages,
    get_messages_v2,
)
from ogn_tool.domain.station_registry import get_station_metadata, list_station_registry, load_station_registry
from ogn_tool.data.packets_repository import make_packets_repository, resolve_db_files

logger = logging.getLogger(__name__)

HOST = "127.0.0.1"
PORT = 8000


def _is_port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex((host, port)) == 0


if _is_port_in_use(HOST, PORT):
    print(f"[ERROR] Port {PORT} already in use on {HOST}.")
    print("Another instance of the API is likely already running.")
    print("Stop it or restart your environment, then run again.")
    sys.exit(1)

app = FastAPI()
collector_process = None

CONFIG_PATH = Path('config/runtime.json')
DEFAULT_RUNTIME_CONFIG = {
    'ogn_user': 'NOCALL',
    'ogn_pass': '-1',
    'ogn_filter': '',
    'db_path': 'ogn_log.sqlite3',
}


def load_runtime_config() -> dict[str, Any]:
    cfg = dict(DEFAULT_RUNTIME_CONFIG)
    if not CONFIG_PATH.exists():
        return cfg

    try:
        with CONFIG_PATH.open('r', encoding='utf-8') as handle:
            data = json.load(handle)
    except Exception:
        return cfg

    if isinstance(data, dict):
        cfg.update({k: v for k, v in data.items() if v is not None})
    return cfg


def resolve_db_path() -> str:
    cfg = load_runtime_config()
    return str(cfg.get('db_path') or DEFAULT_RUNTIME_CONFIG['db_path'])


def _lock_path() -> Path:
    return Path(f"{resolve_db_path()}.collector.lock")


def detect_timestamp_column(cursor: sqlite3.Cursor) -> tuple[str | None, str | None]:
    cursor.execute('PRAGMA table_info(packets)')
    cols = [row[1] for row in cursor.fetchall()]
    if 'ts_epoch' in cols:
        return 'ts_epoch', 'epoch'
    if 'timestamp' in cols:
        return 'timestamp', 'datetime'
    return None, None


def detect_storage_mode(db_path: Path) -> str:
    if db_path.is_dir():
        return 'partitioned'
    if db_path.is_file():
        return 'monolithic'
    return 'unknown'


def compute_db_size_mb(db_path: Path) -> float:
    if db_path.is_file():
        return round(db_path.stat().st_size / (1024 * 1024), 1)

    if db_path.is_dir():
        total_size = sum(p.stat().st_size for p in db_path.rglob('*.sqlite3') if p.is_file())
        return round(total_size / (1024 * 1024), 1)

    return 0.0


def _query_packets_window_stats(cursor: sqlite3.Cursor, column: str, column_type: str) -> dict[str, Any]:
    cursor.execute(f'SELECT MAX({column}) FROM packets')
    last_ts = cursor.fetchone()[0]

    if column_type == 'epoch':
        now_epoch = int(datetime.now(timezone.utc).timestamp())
        t5 = now_epoch - 300
        t1h = now_epoch - 3600

        cursor.execute(f'SELECT COUNT(*) FROM packets WHERE {column} > ?', (t5,))
        last_5min = cursor.fetchone()[0]

        cursor.execute(f'SELECT COUNT(*) FROM packets WHERE {column} > ?', (t1h,))
        last_1h = cursor.fetchone()[0]
    else:
        cursor.execute(f"SELECT COUNT(*) FROM packets WHERE {column} > datetime('now', '-5 minutes')")
        last_5min = cursor.fetchone()[0]

        cursor.execute(f"SELECT COUNT(*) FROM packets WHERE {column} > datetime('now', '-1 hour')")
        last_1h = cursor.fetchone()[0]

    return {
        'last_ts': last_ts,
        'last_5min': last_5min,
        'last_1h': last_1h,
    }


def _runtime_packet_stats(db_path: Path) -> dict[str, Any]:
    result = {
        'last_ts': None,
        'last_5min': None,
        'last_1h': None,
    }

    if not db_path.exists():
        return result

    if db_path.is_file():
        conn = sqlite3.connect(str(db_path), timeout=10)
        try:
            cur = conn.cursor()
            col, col_type = detect_timestamp_column(cur)
            if not col:
                return result
            return _query_packets_window_stats(cur, col, col_type)
        finally:
            conn.close()

    if db_path.is_dir():
        now_epoch = int(datetime.now(timezone.utc).timestamp())
        start_epoch = now_epoch - 3600
        db_files = resolve_db_files(str(db_path), start_epoch, now_epoch)
        if not db_files:
            return result

        total_5min = 0
        total_1h = 0
        last_ts = None

        for db_file in db_files:
            conn = sqlite3.connect(str(db_file), timeout=10)
            try:
                cur = conn.cursor()
                col, col_type = detect_timestamp_column(cur)
                if not col:
                    continue
                stats = _query_packets_window_stats(cur, col, col_type)
                if stats['last_5min'] is not None:
                    total_5min += int(stats['last_5min'])
                if stats['last_1h'] is not None:
                    total_1h += int(stats['last_1h'])
                candidate = stats['last_ts']
                if candidate is not None and (last_ts is None or candidate > last_ts):
                    last_ts = candidate
            finally:
                conn.close()

        result['last_ts'] = last_ts
        result['last_5min'] = total_5min
        result['last_1h'] = total_1h

    return result

RUNS_DIRS = [
    Path('data/runs/analysis_runs'),
    Path('analysis_runs'),
]

STATION_REGISTRY = load_station_registry()

MAX_AIRCRAFT_POINTS = 5000


def _pid_is_alive(pid: int) -> bool:
    if pid is None or pid <= 0:
        return False

    if sys.platform == 'win32':
        try:
            result = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}'],
                capture_output=True,
                text=True,
                timeout=1,
            )
            return f" {pid} " in result.stdout or result.stdout.strip().endswith(str(pid))
        except Exception:
            return False
    else:
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False


def _get_lock_pid() -> int | None:
    try:
        with _lock_path().open('r', encoding='utf-8') as f:
            content = f.read()
            if content.startswith('pid='):
                return int(content.split('=', 1)[1].strip())
    except Exception:
        return None
    return None


def _is_collector_locked() -> bool:
    path = _lock_path()

    if not path.exists():
        return False

    pid = _get_lock_pid()

    if pid is None:
        return True

    if _pid_is_alive(pid):
        return True

    try:
        path.unlink()
    except Exception:
        pass

    return False


def start_collector() -> dict[str, Any]:
    global collector_process

    if _is_collector_locked():
        return {'status': 'already_running', 'reason': 'lock_file_present'}

    collector_process = subprocess.Popen(
        [sys.executable, 'scripts/collector.py'],
        cwd=Path.cwd(),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    time.sleep(0.2)

    if collector_process.poll() is not None:
        return {'status': 'failed_to_start'}

    return {'status': 'started', 'pid': collector_process.pid}


def stop_collector() -> dict[str, Any]:
    global collector_process

    if not _is_collector_locked():
        return {'status': 'not_running'}

    if collector_process and collector_process.poll() is None:
        collector_process.terminate()
        return {'status': 'stopped', 'mode': 'local_process'}

    return {'status': 'running', 'mode': 'external_process'}


def collector_status() -> dict[str, Any]:
    if not _is_collector_locked():
        return {'running': False}

    pid = _get_lock_pid()

    return {
        'running': True,
        'pid': pid,
        'source': 'lock_file',
    }


@app.on_event('startup')
def startup_event() -> None:
    try:
        if not _is_collector_locked():
            start_collector()
    except Exception:
        pass


def _resolve_report_path(run_id: str) -> Path | None:
    for root in RUNS_DIRS:
        candidate = root / run_id / 'report.json'
        if candidate.exists():
            return candidate
    return None


def _load_run_metadata(report_path: Path) -> dict[str, Any]:
    metadata_path = report_path.parent / 'run_metadata.json'
    if not metadata_path.exists():
        return {}

    try:
        with metadata_path.open('r', encoding='utf-8') as handle:
            data = json.load(handle)
    except Exception:
        return {}

    if not isinstance(data, dict):
        return {}
    return data


def _parse_iso_to_epoch(value: Any) -> int | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def _get_primary_station_coords(metadata_doc: dict[str, Any]) -> tuple[str | None, float | None, float | None]:
    meta = metadata_doc.get('metadata') if isinstance(metadata_doc.get('metadata'), dict) else {}
    station_id = meta.get('station_id') if isinstance(meta.get('station_id'), str) else None

    lat = meta.get('station_lat')
    lon = meta.get('station_lon')

    try:
        lat_num = float(lat) if lat is not None else None
        lon_num = float(lon) if lon is not None else None
    except (TypeError, ValueError):
        lat_num = None
        lon_num = None

    return station_id, lat_num, lon_num


def _enrich_station_coordinates(payload: dict[str, Any], report_path: Path) -> dict[str, Any]:
    stations = payload.get('stations')
    if not isinstance(stations, list):
        return payload

    metadata_doc = _load_run_metadata(report_path)
    primary_station_id, primary_lat, primary_lon = _get_primary_station_coords(metadata_doc)

    reference_station_id = payload.get('reference_station_id')
    if not isinstance(reference_station_id, str) and primary_station_id:
        payload['reference_station_id'] = primary_station_id

    for row in stations:
        if not isinstance(row, dict):
            continue

        station_id = row.get('station_id')
        if not isinstance(station_id, str):
            continue

        # Preserve existing coordinates if already present.
        if isinstance(row.get('lat'), (int, float)) and isinstance(row.get('lon'), (int, float)):
            continue

        coords = STATION_REGISTRY.get(station_id.upper())

        if station_id == primary_station_id and primary_lat is not None and primary_lon is not None:
            row['lat'] = primary_lat
            row['lon'] = primary_lon
        elif coords:
            row['lat'] = coords['lat']
            row['lon'] = coords['lon']

    return payload


def _merge_station_sources(payload: dict[str, Any]) -> list[dict[str, Any]]:
    payload_rows = payload.get('stations') if isinstance(payload.get('stations'), list) else []
    merged: dict[str, dict[str, Any]] = {}

    for row in list_station_registry():
        station_id = row.get('station_id')
        if isinstance(station_id, str):
            merged[station_id] = dict(row)

    for row in payload_rows:
        if not isinstance(row, dict):
            continue
        station_id = row.get('station_id')
        if not isinstance(station_id, str):
            continue
        base = dict(merged.get(station_id, {}))
        base.update(row)
        merged[station_id] = base

    return [merged[key] for key in sorted(merged.keys())]


def _load_packet_rows_for_observations(metadata_doc: dict[str, Any]) -> list[dict[str, Any]]:
    meta = metadata_doc.get('metadata') if isinstance(metadata_doc.get('metadata'), dict) else {}
    comparability = metadata_doc.get('comparability') if isinstance(metadata_doc.get('comparability'), dict) else {}

    db_path_value = meta.get('db_path')
    station_id = meta.get('station_id')
    start_iso = comparability.get('time_window_start')
    end_iso = comparability.get('time_window_end')

    if not isinstance(db_path_value, str) or not db_path_value:
        return []
    if not isinstance(station_id, str) or not station_id:
        return []

    start_epoch = _parse_iso_to_epoch(start_iso)
    end_epoch = _parse_iso_to_epoch(end_iso)
    if start_epoch is None or end_epoch is None or end_epoch <= start_epoch:
        return []

    db_path = Path(db_path_value)
    if not db_path.exists():
        return []

    try:
        repo = make_packets_repository(str(db_path))
        return repo.get_packets_for_station_window(start_epoch, end_epoch, station_id)
    except Exception:
        logger.exception(
            'Failed to load packets for station observation window station=%s db_path=%s window=[%s,%s)',
            station_id,
            db_path,
            start_epoch,
            end_epoch,
        )
        return []


def _extract_aircraft_observations(metadata_doc: dict[str, Any], packets: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    packets = packets if packets is not None else _load_packet_rows_for_observations(metadata_doc)
    if not packets:
        return []

    observations = build_aircraft_observations(
        packets,
        temporal_threshold_s=10,
        max_cluster_radius_km=20.0,
    )
    if len(observations) > MAX_AIRCRAFT_POINTS:
        return observations[:MAX_AIRCRAFT_POINTS]
    return observations






def _messages_from_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    metrics = payload.get('metrics') if isinstance(payload.get('metrics'), dict) else {}
    observations = metrics.get('aircraft_positions') if isinstance(metrics.get('aircraft_positions'), list) else []

    out: list[dict[str, Any]] = []
    for idx, obs in enumerate(observations):
        if not isinstance(obs, dict):
            continue
        receivers = obs.get('seen_by') if isinstance(obs.get('seen_by'), list) else []
        out.append(
            {
                'id': obs.get('id') or f'msg_{idx}',
                'timestamp': obs.get('timestamp') or obs.get('timestamp_epoch'),
                'aircraft': obs.get('aircraft_id') or obs.get('src'),
                'type': obs.get('type') or 'RF_OBSERVATION',
                'receivers': receivers,
                'lat': obs.get('lat'),
                'lon': obs.get('lon'),
            }
        )
    return out
def _build_payload_for_run(run_id: str) -> dict[str, Any]:
    report_path = _resolve_report_path(run_id)
    if report_path is None:
        raise HTTPException(status_code=404, detail='run not found')

    report = load_report_from_path(str(report_path))
    if report is None:
        raise HTTPException(status_code=500, detail='invalid report')

    metadata_doc = _load_run_metadata(report_path)
    packet_rows = _load_packet_rows_for_observations(metadata_doc)
    aircraft_observations = _extract_aircraft_observations(metadata_doc, packets=packet_rows)
    if aircraft_observations:
        report = dict(report)
        report['aircraft_observations'] = aircraft_observations

    payload = build_dashboard_payload(report)
    if not isinstance(payload, dict):
        raise HTTPException(status_code=500, detail='invalid payload')

    payload = _enrich_station_coordinates(payload, report_path)
    payload['stations'] = _merge_station_sources(payload)

    meta = metadata_doc.get('metadata') if isinstance(metadata_doc.get('metadata'), dict) else {}
    payload['analysis_mode'] = str(meta.get('analysis_mode') or 'observed')

    metrics = payload.get('metrics')
    if not isinstance(metrics, dict):
        metrics = {}
        payload['metrics'] = metrics
    metrics['aircraft_positions'] = project_aircraft_positions(aircraft_observations)
    metrics['rf_observations'] = packet_rows

    return payload


def _list_runs() -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for root in RUNS_DIRS:
        if not root.exists():
            continue
        for run_dir in root.iterdir():
            if not run_dir.is_dir():
                continue
            report_path = run_dir / 'report.json'
            if not report_path.exists():
                continue

            metadata_doc = _load_run_metadata(report_path)
            comparability = metadata_doc.get('comparability') if isinstance(metadata_doc.get('comparability'), dict) else {}
            meta = metadata_doc.get('metadata') if isinstance(metadata_doc.get('metadata'), dict) else {}

            station = meta.get('station_id') if isinstance(meta.get('station_id'), str) else None
            start = comparability.get('time_window_start') if isinstance(comparability.get('time_window_start'), str) else None
            end = comparability.get('time_window_end') if isinstance(comparability.get('time_window_end'), str) else None

            records.append(
                {
                    'run_id': run_dir.name,
                    'station': station or 'UNKNOWN',
                    'time_window_start': start,
                    'time_window_end': end,
                    'updated_at': datetime.fromtimestamp(report_path.stat().st_mtime, tz=timezone.utc).isoformat(),
                }
            )

    records.sort(key=lambda row: row.get('updated_at') or '', reverse=True)
    return records


class RunExecuteRequest(BaseModel):
    station: str = Field(default='FK50887')
    window_hours: int = Field(default=6, ge=1, le=168)
    end_offset_hours: int = Field(default=0, ge=0, le=720)


@app.get('/api/runs')
def list_runs() -> list[dict[str, Any]]:
    return _list_runs()


@app.get('/api/stations')
def list_stations() -> list[dict[str, Any]]:
    return list_station_registry()


@app.get('/api/runs/{run_id}')
def get_run(run_id: str) -> dict[str, Any]:
    return _build_payload_for_run(run_id)


@app.post('/api/runs/execute')
def execute_run(req: RunExecuteRequest) -> dict[str, Any]:
    station = req.station.strip().upper()
    station_meta = get_station_metadata(station)
    if station_meta is None:
        raise HTTPException(status_code=400, detail='unknown station_id: not found in station registry')

    cmd = [
        sys.executable,
        'scripts/run_fk50887_station.py',
        '--station-id',
        station,
        '--window-hours',
        str(req.window_hours),
        '--end-offset-hours',
        str(req.end_offset_hours),
    ]

    proc = subprocess.run(cmd, cwd=Path.cwd(), capture_output=True, text=True)
    if proc.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail={
                'message': 'run execution failed',
                'stderr': proc.stderr[-4000:],
                'stdout': proc.stdout[-4000:],
            },
        )

    run_id = None
    for line in proc.stdout.splitlines():
        if 'Bundle written to:' in line:
            try:
                run_id = Path(line.split('Bundle written to:', 1)[1].strip()).name
            except Exception:
                run_id = None

    if not run_id:
        runs = _list_runs()
        run_id = runs[0]['run_id'] if runs else None

    if not run_id:
        raise HTTPException(status_code=500, detail='run execution completed but run_id could not be resolved')

    return {'run_id': run_id, 'station': station, 'window_hours': req.window_hours, 'end_offset_hours': req.end_offset_hours}




@app.get('/analysis/{run_id}/rf-field')
def analysis_rf_field(run_id: str) -> dict[str, Any]:
    payload = _build_payload_for_run(run_id)
    return get_rf_field(payload)


@app.get('/analysis/{run_id}/blind-zones')
def analysis_blind_zones(run_id: str) -> dict[str, Any]:
    payload = _build_payload_for_run(run_id)
    return get_blind_zones(payload)


@app.get('/analysis/{run_id}/directional')
def analysis_directional(run_id: str) -> dict[str, Any]:
    payload = _build_payload_for_run(run_id)
    return get_directional(payload)


@app.get('/analysis/{run_id}/visibility')
def analysis_visibility(run_id: str) -> dict[str, Any]:
    payload = _build_payload_for_run(run_id)
    return get_visibility(payload)


@app.get('/analysis/{run_id}/quality')
def analysis_quality(run_id: str) -> dict[str, Any]:
    payload = _build_payload_for_run(run_id)
    return get_rf_quality(payload)


@app.get('/analysis/{run_id}/timeseries')
def analysis_timeseries(run_id: str) -> dict[str, Any]:
    payload = _build_payload_for_run(run_id)
    return get_timeseries(payload)


@app.get('/analysis/{run_id}/diagnosis')
def analysis_diagnosis(run_id: str) -> dict[str, Any]:
    payload = _build_payload_for_run(run_id)
    return get_diagnosis(payload)


@app.get('/analysis/{run_id}/messages')
def analysis_messages(run_id: str) -> dict[str, Any]:
    payload = _build_payload_for_run(run_id)
    return get_messages(payload)


@app.get('/analysis/{run_id}/messages_v2')
def analysis_messages_v2(run_id: str) -> dict[str, Any]:
    payload = _build_payload_for_run(run_id)
    logger.info('Serving messages_v2 for run_id=%s', run_id)
    return get_messages_v2(payload)

@app.get('/api/runtime/status')
def api_runtime_status() -> dict[str, Any]:
    db_path_value = resolve_db_path()
    db_path = Path(db_path_value)

    cfg = load_runtime_config()

    result = {
        'collector': {
            'running': False,
            'pid': None,
            'user': cfg.get('ogn_user'),
            'filter': cfg.get('ogn_filter') or '',
        },
        'db': {
            'path': str(db_path),
            'exists': db_path.exists(),
            'size_mb': compute_db_size_mb(db_path),
            'mode': detect_storage_mode(db_path),
        },
        'packets': {
            'last_ts': None,
            'last_5min': None,
            'last_1h': None,
        },
    }

    collector = collector_status()
    result['collector']['running'] = bool(collector.get('running'))
    result['collector']['pid'] = collector.get('pid')

    if not db_path.exists():
        return result

    try:
        result['packets'] = _runtime_packet_stats(db_path)
    except Exception as exc:
        result['error'] = str(exc)

    return result


@app.get('/collector/status')
def api_collector_status() -> dict[str, Any]:
    return collector_status()


@app.post('/collector/start')
def api_collector_start() -> dict[str, Any]:
    return start_collector()


@app.post('/collector/stop')
def api_collector_stop() -> dict[str, Any]:
    return stop_collector()


@app.get('/api/payload')
def get_payload(run_id: str = Query(..., min_length=1)) -> dict:
    return _build_payload_for_run(run_id)


app.mount('/', StaticFiles(directory='frontend', html=True), name='frontend')
