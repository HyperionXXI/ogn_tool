from __future__ import annotations

import logging
import sqlite3
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def load_packets_window(
    db_path: str,
    since_iso: str,
    since_epoch: int,
    dst_types,
    station_callsign: str,
    only_heard_by: bool,
    igate_filter: str,
    source_mode: str,
    qas_filter: str,
    limit_rows: int,
    query_log: Optional[List[Dict]] = None,
) -> pd.DataFrame:
    q = ["SELECT * FROM packets WHERE ts_epoch >= ?"]
    params: List[object] = [int(since_epoch)]

    if station_callsign and (only_heard_by or igate_filter):
        target = station_callsign if only_heard_by else igate_filter
        q.append("AND igate = ?")
        params.append(str(target).strip().upper())

    if qas_filter:
        q.append("AND UPPER(COALESCE(qas, '')) = UPPER(?)")
        params.append(str(qas_filter))

    if dst_types:
        dst = list(dst_types)
        placeholders = ",".join(["?"] * len(dst))
        q.append(f"AND UPPER(COALESCE(dst, '')) IN ({placeholders})")
        params.extend([str(x).upper() for x in dst])

    q.append("ORDER BY ts_epoch DESC")
    q.append("LIMIT ?")
    params.append(int(limit_rows))

    sql = " ".join(q)
    if query_log is not None:
        query_log.append({"sql": sql, "params": params})

    with sqlite3.connect(db_path, timeout=10) as con:
        return pd.read_sql_query(sql, con, params=params)



class PacketsRepository:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path, timeout=10)
        con.row_factory = sqlite3.Row
        return con

    def _packet_columns(self) -> set[str]:
        with self._connect() as con:
            return {str(row['name']).lower() for row in con.execute('PRAGMA table_info(packets)').fetchall()}

    def get_packets_for_station_window(
        self,
        start_epoch: int,
        end_epoch: int,
        station_id: str,
    ) -> list[dict[str, Any]]:
        started_at = time.perf_counter()
        station_id = station_id.strip().upper()

        packet_columns = self._packet_columns()
        optional_columns = [col for col in ('rssi', 'snr', 'raw') if col in packet_columns]
        has_rssi = 'rssi' in packet_columns
        has_snr = 'snr' in packet_columns
        has_raw = 'raw' in packet_columns
        select_columns = ['src', 'lat', 'lon', 'ts_epoch', 'igate', *optional_columns]
        select_clause = ', '.join(select_columns)

        packets: list[dict[str, Any]] = []
        with self._connect() as con:
            for row in con.execute(
                f'''
                SELECT {select_clause}
                FROM packets
                WHERE ts_epoch >= ?
                  AND ts_epoch < ?
                  AND igate = ?
                  AND lat IS NOT NULL
                  AND lon IS NOT NULL
                  AND src IS NOT NULL
                ''',
                (start_epoch, end_epoch, station_id),
            ):
                packets.append(
                    {
                        'src': row['src'],
                        'lat': row['lat'],
                        'lon': row['lon'],
                        'ts_epoch': row['ts_epoch'],
                        'igate': row['igate'],
                        'rssi': row['rssi'] if has_rssi else None,
                        'snr': row['snr'] if has_snr else None,
                        'raw': row['raw'] if has_raw else None,
                    }
                )

        elapsed_ms = (time.perf_counter() - started_at) * 1000
        logger.info(
            'PacketsRepository loaded %s packets for station=%s window=[%s,%s) in %.1f ms',
            len(packets),
            station_id,
            start_epoch,
            end_epoch,
            elapsed_ms,
        )
        return packets



def resolve_db_files(base_path: str, start_epoch: int, end_epoch: int) -> list[Path]:
    base = Path(base_path)

    start = datetime.utcfromtimestamp(start_epoch).date()
    end = datetime.utcfromtimestamp(end_epoch).date()

    files: list[Path] = []
    current = start
    while current <= end:
        db_path = (
            base
            / f"{current.year:04d}"
            / f"{current.month:02d}"
            / f"{current.day:02d}.sqlite3"
        )
        if db_path.exists():
            files.append(db_path)
        current += timedelta(days=1)

    return files


class PartitionedPacketsRepository:
    def __init__(self, base_path: str):
        self.base_path = base_path
        self._columns_cache: dict[Path, set[str]] = {}

    def _connect(self, db_path: Path) -> sqlite3.Connection:
        con = sqlite3.connect(str(db_path), timeout=10)
        con.row_factory = sqlite3.Row
        return con

    def _packet_columns(self, db_path: Path) -> set[str]:
        if db_path in self._columns_cache:
            return self._columns_cache[db_path]

        with self._connect(db_path) as con:
            cols = {
                str(row['name']).lower()
                for row in con.execute('PRAGMA table_info(packets)').fetchall()
            }
        self._columns_cache[db_path] = cols
        return cols

    def _load_packets_from_file(
        self,
        db_file: Path,
        start_epoch: int,
        end_epoch: int,
        station_id: str,
    ) -> list[dict[str, Any]]:
        packet_columns = self._packet_columns(db_file)
        optional_columns = [c for c in ('rssi', 'snr', 'raw') if c in packet_columns]
        has_rssi = 'rssi' in packet_columns
        has_snr = 'snr' in packet_columns
        has_raw = 'raw' in packet_columns
        select_cols = ['src', 'lat', 'lon', 'ts_epoch', 'igate', *optional_columns]
        select_clause = ', '.join(select_cols)

        packets: list[dict[str, Any]] = []
        with self._connect(db_file) as con:
            for row in con.execute(
                f'''
                SELECT {select_clause}
                FROM packets
                WHERE ts_epoch >= ?
                  AND ts_epoch < ?
                  AND igate = ?
                  AND lat IS NOT NULL
                  AND lon IS NOT NULL
                  AND src IS NOT NULL
                ''',
                (start_epoch, end_epoch, station_id),
            ):
                packets.append(
                    {
                        'src': row['src'],
                        'lat': row['lat'],
                        'lon': row['lon'],
                        'ts_epoch': row['ts_epoch'],
                        'igate': row['igate'],
                        'rssi': row['rssi'] if has_rssi else None,
                        'snr': row['snr'] if has_snr else None,
                        'raw': row['raw'] if has_raw else None,
                    }
                )
        return packets

    def get_packets_for_station_window(
        self,
        start_epoch: int,
        end_epoch: int,
        station_id: str,
    ) -> list[dict[str, Any]]:
        started_at = time.perf_counter()
        station_id = station_id.strip().upper()
        db_files = resolve_db_files(self.base_path, start_epoch, end_epoch)

        if not db_files:
            logger.info(
                'PartitionedPacketsRepository found no DB files for station=%s window=[%s,%s)',
                station_id,
                start_epoch,
                end_epoch,
            )
            return []

        all_packets: list[dict[str, Any]] = []
        files_read = 0
        max_workers = min(4, len(db_files))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._load_packets_from_file, db_file, start_epoch, end_epoch, station_id): db_file
                for db_file in db_files
            }

            for future in as_completed(futures):
                db_file = futures[future]
                try:
                    packets = future.result()
                    files_read += 1
                    all_packets.extend(packets)
                except Exception as exc:
                    logger.warning('Failed reading DB file %s: %s', db_file, exc)

        all_packets.sort(key=lambda x: x['ts_epoch'], reverse=True)
        elapsed_ms = (time.perf_counter() - started_at) * 1000
        logger.info(
            'PartitionedPacketsRepository loaded %s packets from %s/%s files for station=%s window=[%s,%s) in %.1f ms',
            len(all_packets),
            files_read,
            len(db_files),
            station_id,
            start_epoch,
            end_epoch,
            elapsed_ms,
        )
        return all_packets


def make_packets_repository(path: str):
    p = Path(path)

    if p.is_file():
        return PacketsRepository(str(p))

    if p.is_dir():
        return PartitionedPacketsRepository(str(p))

    raise ValueError(f'Invalid DB path: {path}')
