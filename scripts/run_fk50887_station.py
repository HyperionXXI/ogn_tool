from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

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
AZIMUTH_BINS = [float(value) for value in range(0, 361, 10)]
DISTANCE_BINS_KM = [float(value) for value in range(0, 151, 10)]


def _build_azimuth_distance_surface(packets):
    observations = packets.copy()
    observations['distance_km'] = compute_distance(observations, STATION_LAT, STATION_LON)
    observations['bearing_deg'] = compute_bearing(observations, STATION_LAT, STATION_LON)

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
        end_epoch=int(end_dt.timestamp()),
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
    azimuth_distance_surface = _build_azimuth_distance_surface(packets)
    report.rf_signature = dict(azimuth_distance_surface.get('summary', {}).get('rf_signature') or {})

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
    registry_dir = Path("data/runs/analysis_runs")
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
        additional_artifacts={
            'azimuth_distance_surface': azimuth_distance_surface,
        },
    )
    register_run(bundle_dir, registry_dir)

    print(f"Bundle written to: {bundle_dir}")
    print(f"Packets loaded: {len(packets)}")
    print(f"Window start: {time_start}")
    print(f"Window end:   {time_end}")
    print(f"Freshness lag (h): {lag_hours}")
    print(f"Station analysis keys: {list((station_analysis or {}).keys())}")
    print(f"Network analysis keys: {list((network_analysis or {}).keys())}")
    print(f"Azimuth-distance packets represented: {azimuth_distance_surface['packet_count']}")
    if isinstance(network_analysis, dict) and isinstance(network_analysis.get("network_metrics"), dict):
        print(f"network_metrics keys: {list(network_analysis['network_metrics'].keys())}")


if __name__ == "__main__":
    main()
