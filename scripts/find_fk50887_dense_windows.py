from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

import pandas as pd

DB_PATH = Path(r"F:\Data\ogn\ogn_log.sqlite3")
STATION_ID = "FK50887"
DEFAULT_WINDOW_HOURS = 72
DEFAULT_TOP = 10


def main() -> None:
    parser = argparse.ArgumentParser(description='Find dense historical windows for FK50887')
    parser.add_argument('--db-path', default=str(DB_PATH))
    parser.add_argument('--station-id', default=STATION_ID)
    parser.add_argument('--window-hours', type=int, default=DEFAULT_WINDOW_HOURS)
    parser.add_argument('--top', type=int, default=DEFAULT_TOP)
    args = parser.parse_args()

    with sqlite3.connect(args.db_path) as con:
        frame = pd.read_sql_query(
            "SELECT ts_epoch FROM packets WHERE UPPER(COALESCE(igate, '')) = UPPER(?) ORDER BY ts_epoch ASC",
            con,
            params=[args.station_id],
        )

    if frame.empty:
        raise SystemExit(f'No packets found for station {args.station_id}.')

    frame['ts'] = pd.to_datetime(frame['ts_epoch'], unit='s', utc=True)
    hourly = frame.set_index('ts').resample('1H').size().rename('packet_count')
    rolling = hourly.rolling(args.window_hours, min_periods=args.window_hours).sum().dropna()

    if rolling.empty:
        raise SystemExit('Not enough history to compute the requested rolling window.')

    top = rolling.sort_values(ascending=False).head(args.top)
    latest_ts = frame['ts'].max()

    print(f'Station: {args.station_id}')
    print(f'DB path: {args.db_path}')
    print(f'Window hours: {args.window_hours}')
    print(f'Latest packet: {latest_ts.isoformat()}')
    print('Top dense windows:')

    for end_ts, packet_count in top.items():
        start_ts = end_ts - pd.Timedelta(hours=args.window_hours)
        offset_hours = int((latest_ts - end_ts).total_seconds() // 3600)
        print(
            f'- packets={int(packet_count):6d} '
            f'start={start_ts.isoformat()} '
            f'end={end_ts.isoformat()} '
            f'end_offset_hours={offset_hours}'
        )


if __name__ == '__main__':
    main()
