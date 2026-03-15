from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ogn_tool.analysis.dataset_identity import build_dataset_identity
from ogn_tool.reporting import (
    build_network_engineering_report,
    build_run_comparability,
    export_analysis_run_bundle,
)
from ogn_tool.reporting.run_registry import register_run
from ogn_tool.services import rf_analysis_service

DB_PATH = r"F:\Data\ogn\ogn_log.sqlite3"
STATION_ID = "FK50887"

# GXAirCom station coordinates.
STATION_LAT = 47.335831
STATION_LON = 7.273000
STATION_ALT_M = 454.1

DEFAULT_WINDOW_HOURS = 72
LIMIT_ROWS = 100000
ANALYSIS_VERSION = "2026.03"
CONFIG_IDENTITY = "fk50887_station_v1"


def main() -> None:
    """Run a reproducible station-focused analysis for FK50887."""
    parser = argparse.ArgumentParser(description="Run FK50887 station analysis")
    parser.add_argument(
        "--window-hours",
        type=int,
        default=DEFAULT_WINDOW_HOURS,
        help="Time window for analysis in hours",
    )
    parser.add_argument(
        "--end-offset-hours",
        type=int,
        default=0,
        help="Offset the analysis end time backward from db_max_ts in hours",
    )
    args = parser.parse_args()
    window_hours = args.window_hours
    end_offset_hours = args.end_offset_hours

    max_ts = rf_analysis_service.db_max_ts_epoch(DB_PATH)
    if not max_ts:
        raise SystemExit("No timestamp found in database.")

    end_dt = datetime.fromtimestamp(int(max_ts), tz=timezone.utc) - timedelta(hours=end_offset_hours)
    start_dt = end_dt - timedelta(hours=window_hours)

    packets = rf_analysis_service.load_rf_receptions(
        db_path=DB_PATH,
        since_epoch=int(start_dt.timestamp()),
        limit_rows=LIMIT_ROWS,
        station_id=STATION_ID,
    )
    if packets.empty:
        raise SystemExit(f"No RF receptions found for {STATION_ID}.")

    rf_analysis_service.build_rf_dataset(
        packets_df=packets,
        station_lat=STATION_LAT,
        station_lon=STATION_LON,
        dataset_mode="NETWORK",
        station_id=STATION_ID,
    )

    station_analysis = rf_analysis_service.run_station_analysis(
        dataset_mode="NETWORK",
        station_id=STATION_ID,
    )
    network_analysis = rf_analysis_service.run_network_analysis(
        dataset_mode="NETWORK",
        station_id=STATION_ID,
    )

    report = build_network_engineering_report(
        network_analysis.get("network_metrics") if isinstance(network_analysis, dict) else {},
        network_analysis.get("spatial_observations") if isinstance(network_analysis, dict) else None,
    )

    time_start = start_dt.isoformat(timespec="seconds").replace("+00:00", "Z")
    time_end = end_dt.isoformat(timespec="seconds").replace("+00:00", "Z")

    dataset_identity = build_dataset_identity(
        packet_count=len(packets),
        time_start=time_start,
        time_end=time_end,
        source="ogn_sqlite",
    )
    comparability = build_run_comparability(
        analysis_version=ANALYSIS_VERSION,
        time_window_start=time_start,
        time_window_end=time_end,
        config_identity=CONFIG_IDENTITY,
    )

    lag_hours = int((datetime.now(timezone.utc) - end_dt).total_seconds() // 3600)

    run_id = end_dt.strftime(f"fk50887_%Y_%m_%d_%H%M%S_{window_hours}h_offset{end_offset_hours}h")
    registry_dir = Path("analysis_runs")
    bundle_dir = registry_dir / run_id

    export_analysis_run_bundle(
        report,
        bundle_dir,
        run_metadata={
            "station_id": STATION_ID,
            "analysis_scope": "station_signature",
            "window_hours": window_hours,
            "end_offset_hours": end_offset_hours,
            "db_path": DB_PATH,
            "data_freshness_lag_hours": lag_hours,
        },
        dataset_identity=dataset_identity,
        comparability=comparability,
    )
    register_run(bundle_dir, registry_dir)

    print(f"Bundle written to: {bundle_dir}")
    print(f"Packets loaded: {len(packets)}")
    print(f"Window start: {time_start}")
    print(f"Window end:   {time_end}")
    print(f"Freshness lag (h): {lag_hours}")
    print(f"Station analysis keys: {list((station_analysis or {}).keys())}")
    print(f"Network analysis keys: {list((network_analysis or {}).keys())}")
    if isinstance(network_analysis, dict) and isinstance(network_analysis.get("network_metrics"), dict):
        print(f"network_metrics keys: {list(network_analysis['network_metrics'].keys())}")


if __name__ == "__main__":
    main()
