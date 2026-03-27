from __future__ import annotations

import argparse
import math
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

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
from ogn_tool.domain.station_registry import get_station_metadata, load_station_registry

DB_PATH = r"F:\Data\ogn\ogn_log.sqlite3"
DEFAULT_station_id = "FK50887"

DEFAULT_WINDOW_HOURS = 72
LIMIT_ROWS = 100000
ANALYSIS_VERSION = "2026.03"
CONFIG_IDENTITY = "fk50887_station_v1"
AZIMUTH_BINS = [float(value) for value in range(0, 361, 10)]
DISTANCE_BINS_KM = [float(value) for value in range(0, 151, 10)]
PREDICTED_NEIGHBOR_RADIUS_KM = 100.0


def _build_azimuth_distance_surface(packets, station_lat: float, station_lon: float):
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


def _distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2.0) ** 2
    )
    return 2.0 * radius_km * math.asin(math.sqrt(a))


def build_predicted_metrics(station_id: str, station_lat: float, station_lon: float) -> dict[str, object]:
    registry = load_station_registry()
    neighbors: list[dict[str, float | str]] = []

    for candidate_id, row in registry.items():
        if candidate_id == station_id:
            continue
        lat = float(row['lat'])
        lon = float(row['lon'])
        distance = _distance_km(station_lat, station_lon, lat, lon)
        if distance <= PREDICTED_NEIGHBOR_RADIUS_KM:
            neighbors.append(
                {
                    'station_id': candidate_id,
                    'distance_km': distance,
                    'lat': lat,
                    'lon': lon,
                }
            )

    neighbors.sort(key=lambda item: float(item['distance_km']))
    neighbor_count = len(neighbors)
    closest_station = neighbors[0] if neighbors else None
    avg_distance_km = (
        sum(float(item['distance_km']) for item in neighbors) / neighbor_count if neighbor_count else None
    )

    coverage_score = min(1.0, neighbor_count / 5.0) if neighbor_count else 0.0
    redundancy_score = min(1.0, neighbor_count / 4.0) if neighbor_count else 0.0
    confidence_score = 0.2

    if coverage_score >= 0.7:
        health_status = 'OK'
    elif coverage_score >= 0.4:
        health_status = 'WARNING'
    else:
        health_status = 'CRITICAL'

    station_health = pd.DataFrame(
        [
            {
                'station_id': station_id,
                'lat': station_lat,
                'lon': station_lon,
                'health_status': health_status,
                'impact_score': round(1.0 - coverage_score, 3),
                'analysis_mode': 'predicted',
            }
        ]
    )

    station_dependency = pd.DataFrame(
        [
            {
                'station_id': station_id,
                'dependency_score': round(1.0 - redundancy_score, 3),
            }
        ]
    )
    station_dominance = pd.DataFrame(
        [
            {
                'station_id': station_id,
                'dominance_ratio': 1.0,
            }
        ]
    )

    network_summary = {
        'station_count': 1,
        'packet_count': 0,
        'coverage_score': coverage_score,
        'neighbor_count': neighbor_count,
        'closest_station_id': closest_station['station_id'] if closest_station else None,
        'closest_station_distance_km': round(float(closest_station['distance_km']), 3) if closest_station else None,
        'avg_neighbor_distance_km': round(float(avg_distance_km), 3) if avg_distance_km is not None else None,
        'analysis_mode': 'predicted',
    }

    network_redundancy = {
        'redundancy_score': redundancy_score,
        'confidence_score': confidence_score,
        'neighbor_count': neighbor_count,
    }
    network_confidence = {
        'confidence_score': confidence_score,
        'confidence_band': 'predicted',
    }
    analysis_stats = {
        'predicted_metrics': {
            'neighbor_count': neighbor_count,
            'closest_station': closest_station,
            'avg_distance_km': round(float(avg_distance_km), 3) if avg_distance_km is not None else None,
        }
    }

    return {
        'network_summary': network_summary,
        'network_redundancy': network_redundancy,
        'network_confidence': network_confidence,
        'station_health': station_health,
        'station_dependency': station_dependency,
        'station_dominance': station_dominance,
        'analysis_stats': analysis_stats,
    }


def main() -> None:
    """Run a reproducible station-focused RF analysis from the station registry."""
    parser = argparse.ArgumentParser(description="Run station RF analysis")
    parser.add_argument(
        "--station-id",
        default=DEFAULT_station_id,
        help="Station ID from the station registry",
    )
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
    station_id = str(args.station_id or DEFAULT_station_id).strip().upper()
    station_meta = get_station_metadata(station_id)
    if station_meta is None:
        raise SystemExit(f'unknown station_id in registry: {station_id}')

    station_lat = float(station_meta['lat'])
    station_lon = float(station_meta['lon'])
    station_alt_m = float(station_meta.get('alt_m') or 0.0)

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
        station_id=station_id,
    )

    analysis_mode = 'observed'
    azimuth_distance_surface: dict[str, object] | None = None

    if packets.empty:
        analysis_mode = 'predicted'
        station_analysis = {}
        network_analysis = {
            'network_metrics': build_predicted_metrics(station_id, station_lat, station_lon),
            'spatial_observations': pd.DataFrame(),
        }
    else:
        rf_analysis_service.build_rf_dataset(
            packets_df=packets,
            station_lat=station_lat,
            station_lon=station_lon,
            dataset_mode="NETWORK",
            station_id=station_id,
        )

        station_analysis = rf_analysis_service.run_station_analysis(
            dataset_mode="NETWORK",
            station_id=station_id,
        )
        network_analysis = rf_analysis_service.run_network_analysis(
            dataset_mode="NETWORK",
            station_id=station_id,
        )
        azimuth_distance_surface = _build_azimuth_distance_surface(packets, station_lat, station_lon)

    report = build_network_engineering_report(
        network_analysis.get("network_metrics") if isinstance(network_analysis, dict) else {},
        network_analysis.get("spatial_observations") if isinstance(network_analysis, dict) else None,
    )

    if analysis_mode == 'observed' and azimuth_distance_surface is not None:
        report.rf_signature = dict(azimuth_distance_surface.get('summary', {}).get('rf_signature') or {})

    time_start = start_dt.isoformat(timespec="seconds").replace("+00:00", "Z")
    time_end = end_dt.isoformat(timespec="seconds").replace("+00:00", "Z")

    dataset_identity = build_dataset_identity(
        packet_count=len(packets),
        time_start=time_start,
        time_end=time_end,
        source="ogn_sqlite" if analysis_mode == 'observed' else 'station_registry_prediction',
    )
    comparability = build_run_comparability(
        analysis_version=ANALYSIS_VERSION,
        time_window_start=time_start,
        time_window_end=time_end,
        config_identity=CONFIG_IDENTITY,
    )

    lag_hours = int((datetime.now(timezone.utc) - end_dt).total_seconds() // 3600)

    run_id = end_dt.strftime(f"{station_id.lower()}_%Y_%m_%d_%H%M%S_{window_hours}h_offset{end_offset_hours}h")
    registry_dir = Path("data/runs/analysis_runs")
    bundle_dir = registry_dir / run_id

    additional_artifacts = {}
    if azimuth_distance_surface is not None:
        additional_artifacts['azimuth_distance_surface'] = azimuth_distance_surface

    export_analysis_run_bundle(
        report,
        bundle_dir,
        run_metadata={
            "station_id": station_id,
            "analysis_scope": "station_signature",
            "analysis_mode": analysis_mode,
            "window_hours": window_hours,
            "end_offset_hours": end_offset_hours,
            "db_path": DB_PATH,
            "data_freshness_lag_hours": lag_hours,
            "station_lat": station_lat,
            "station_lon": station_lon,
            "station_alt_m": station_alt_m,
        },
        dataset_identity=dataset_identity,
        comparability=comparability,
        additional_artifacts=additional_artifacts,
    )
    register_run(bundle_dir, registry_dir)

    print(f"Bundle written to: {bundle_dir}")
    print(f"Packets loaded: {len(packets)}")
    print(f"Analysis mode: {analysis_mode}")
    print(f"Window start: {time_start}")
    print(f"Window end:   {time_end}")
    print(f"Freshness lag (h): {lag_hours}")
    print(f"Station analysis keys: {list((station_analysis or {}).keys())}")
    print(f"Network analysis keys: {list((network_analysis or {}).keys())}")
    if azimuth_distance_surface is not None:
        print(f"Azimuth-distance packets represented: {azimuth_distance_surface['packet_count']}")
    if isinstance(network_analysis, dict) and isinstance(network_analysis.get("network_metrics"), dict):
        print(f"network_metrics keys: {list(network_analysis['network_metrics'].keys())}")


if __name__ == "__main__":
    main()
