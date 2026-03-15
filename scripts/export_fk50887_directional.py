from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from ogn_tool.services import rf_analysis_service

DB_PATH = r"F:\Data\ogn\ogn_log.sqlite3"
STATION_ID = "FK50887"
STATION_LAT = 47.335831
STATION_LON = 7.273000
DEFAULT_WINDOW_HOURS = 24
LIMIT_ROWS = 100000
OUTPUT_ROOT = Path("analysis_directional")


def _write_payload(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(payload, pd.DataFrame):
        payload.to_csv(path.with_suffix('.csv'), index=False)
        return
    with path.with_suffix('.json').open('w', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, default=str)


def main() -> None:
    parser = argparse.ArgumentParser(description='Export FK50887 directional RF surfaces')
    parser.add_argument('--window-hours', type=int, default=DEFAULT_WINDOW_HOURS)
    parser.add_argument('--end-offset-hours', type=int, default=0)
    args = parser.parse_args()

    max_ts = rf_analysis_service.db_max_ts_epoch(DB_PATH)
    if not max_ts:
        raise SystemExit('No timestamp found in database.')

    end_dt = datetime.fromtimestamp(int(max_ts), tz=timezone.utc) - timedelta(hours=args.end_offset_hours)
    start_dt = end_dt - timedelta(hours=args.window_hours)

    packets = rf_analysis_service.load_rf_receptions(
        db_path=DB_PATH,
        since_epoch=int(start_dt.timestamp()),
        end_epoch=int(end_dt.timestamp()),
        limit_rows=LIMIT_ROWS,
        station_id=STATION_ID,
    )
    if packets.empty:
        raise SystemExit(f'No RF receptions found for {STATION_ID}.')

    rf_analysis_service.build_rf_dataset(
        packets_df=packets,
        station_lat=STATION_LAT,
        station_lon=STATION_LON,
        dataset_mode='NETWORK',
        station_id=STATION_ID,
    )

    station_analysis = rf_analysis_service.run_station_analysis(dataset_mode='NETWORK', station_id=STATION_ID)
    network_analysis = rf_analysis_service.run_network_analysis(dataset_mode='NETWORK', station_id=STATION_ID)
    network_metrics = network_analysis.get('network_metrics', {}) if isinstance(network_analysis, dict) else {}

    run_id = end_dt.strftime(f'fk50887_%Y_%m_%d_%H%M%S_{args.window_hours}h_offset{args.end_offset_hours}h')
    output_dir = OUTPUT_ROOT / run_id

    outputs = {
        'azimuth_histogram': station_analysis.get('azimuth_histogram') if isinstance(station_analysis, dict) else None,
        'directional_balance': station_analysis.get('directional_balance') if isinstance(station_analysis, dict) else None,
        'station_angular_entropy': network_metrics.get('station_angular_entropy') if isinstance(network_metrics, dict) else None,
        'shadow_risk_scores': network_metrics.get('shadow_risk_scores') if isinstance(network_metrics, dict) else None,
    }

    for name, payload in outputs.items():
        if payload is None:
            continue
        _write_payload(output_dir / name, payload)

    print(f'Directional outputs written to: {output_dir}')
    print(f'Packets loaded: {len(packets)}')
    print(f'Window start: {start_dt.isoformat(timespec="seconds").replace("+00:00", "Z")}')
    print(f'Window end:   {end_dt.isoformat(timespec="seconds").replace("+00:00", "Z")}')
    print('Written artifacts:')
    for item in sorted(output_dir.iterdir()):
        print(f'- {item.name}')


if __name__ == '__main__':
    main()
