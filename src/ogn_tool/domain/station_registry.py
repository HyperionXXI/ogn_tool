from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REGISTRY_PATH = Path('config/station_registry.json')


def load_station_registry(path: Path | None = None) -> dict[str, dict[str, Any]]:
    registry_path = path or REGISTRY_PATH
    if not registry_path.exists():
        return {}

    try:
        payload = json.loads(registry_path.read_text(encoding='utf-8'))
    except Exception:
        return {}

    rows = payload.get('stations') if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        return {}

    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        station_id = row.get('station_id')
        if not isinstance(station_id, str) or not station_id.strip():
            continue
        try:
            lat = float(row.get('lat'))
            lon = float(row.get('lon'))
        except (TypeError, ValueError):
            continue

        out[station_id.strip().upper()] = {
            'station_id': station_id.strip().upper(),
            'lat': lat,
            'lon': lon,
            'alt_m': row.get('alt_m'),
            'coords_status': row.get('coords_status'),
            'source': row.get('source') or 'station_registry',
        }
    return out


def get_station_metadata(station_id: str, path: Path | None = None) -> dict[str, Any] | None:
    if not isinstance(station_id, str) or not station_id.strip():
        return None
    registry = load_station_registry(path)
    return registry.get(station_id.strip().upper())


def list_station_registry(path: Path | None = None) -> list[dict[str, Any]]:
    registry = load_station_registry(path)
    return [registry[key] for key in sorted(registry.keys())]
