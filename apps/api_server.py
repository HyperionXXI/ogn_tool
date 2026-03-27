from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from ogn_tool.domain.aircraft_observations import (
    build_aircraft_observations,
    project_aircraft_positions,
)
from ogn_tool.reporting.views.dashboard_views import build_dashboard_payload, load_report_from_path

app = FastAPI()

RUNS_DIRS = [
    Path('data/runs/analysis_runs'),
    Path('analysis_runs'),
]

# Minimal fallback map for known local stations used in validation runs.
STATION_COORDS: dict[str, dict[str, float]] = {
    'FK50887': {'lat': 47.335831, 'lon': 7.273000},
    'LSPD': {'lat': 47.300000, 'lon': 7.500000},
    'LSZG': {'lat': 47.181000, 'lon': 7.417000},
    'SOLOTHURN': {'lat': 47.207000, 'lon': 7.537000},
}

MAX_AIRCRAFT_POINTS = 5000


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

        coords = STATION_COORDS.get(station_id)

        if station_id == primary_station_id and primary_lat is not None and primary_lon is not None:
            row['lat'] = primary_lat
            row['lon'] = primary_lon
        elif coords:
            row['lat'] = coords['lat']
            row['lon'] = coords['lon']

    return payload


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
        con = sqlite3.connect(str(db_path), timeout=10)
        con.row_factory = sqlite3.Row
    except Exception:
        return []

    try:
        src_rows = con.execute(
            """
            SELECT DISTINCT src
            FROM packets
            WHERE ts_epoch >= ?
              AND ts_epoch < ?
              AND UPPER(COALESCE(igate, '')) = UPPER(?)
              AND src IS NOT NULL
            """,
            (start_epoch, end_epoch, station_id),
        ).fetchall()
        src_values = sorted(str(row['src']) for row in src_rows if row['src'])

        if not src_values:
            return []

        packets: list[dict[str, Any]] = []
        chunk_size = 500
        for idx in range(0, len(src_values), chunk_size):
            chunk = src_values[idx: idx + chunk_size]
            placeholders = ','.join(['?'] * len(chunk))
            query = f"""
                SELECT src, lat, lon, ts_epoch, igate
                FROM packets
                WHERE ts_epoch >= ?
                  AND ts_epoch < ?
                  AND src IN ({placeholders})
                  AND lat IS NOT NULL
                  AND lon IS NOT NULL
            """
            params: list[Any] = [start_epoch, end_epoch, *chunk]
            for row in con.execute(query, params):
                packets.append(
                    {
                        'src': row['src'],
                        'lat': row['lat'],
                        'lon': row['lon'],
                        'ts_epoch': row['ts_epoch'],
                        'igate': row['igate'],
                    }
                )

        return packets
    except Exception:
        return []
    finally:
        con.close()


def _extract_aircraft_positions(metadata_doc: dict[str, Any]) -> list[dict[str, Any]]:
    packets = _load_packet_rows_for_observations(metadata_doc)
    if not packets:
        return []

    observations = build_aircraft_observations(
        packets,
        temporal_threshold_s=10,
        max_cluster_radius_km=20.0,
    )
    if not observations:
        return []

    projected = project_aircraft_positions(observations)
    if len(projected) > MAX_AIRCRAFT_POINTS:
        return projected[:MAX_AIRCRAFT_POINTS]
    return projected


@app.get('/api/payload')
def get_payload(run_id: str = Query(..., min_length=1)) -> dict:
    report_path = _resolve_report_path(run_id)
    if report_path is None:
        raise HTTPException(status_code=404, detail='run not found')

    report = load_report_from_path(str(report_path))
    if report is None:
        raise HTTPException(status_code=500, detail='invalid report')

    payload = build_dashboard_payload(report)
    if not isinstance(payload, dict):
        raise HTTPException(status_code=500, detail='invalid payload')

    payload = _enrich_station_coordinates(payload, report_path)

    meta = metadata_doc.get('metadata') if isinstance(metadata_doc.get('metadata'), dict) else {}
    payload['analysis_mode'] = str(meta.get('analysis_mode') or 'observed')

    metadata_doc = _load_run_metadata(report_path)
    aircraft_positions = _extract_aircraft_positions(metadata_doc)
    metrics = payload.get('metrics')
    if not isinstance(metrics, dict):
        metrics = {}
        payload['metrics'] = metrics
    metrics['aircraft_positions'] = aircraft_positions

    return payload


app.mount('/', StaticFiles(directory='frontend', html=True), name='frontend')
