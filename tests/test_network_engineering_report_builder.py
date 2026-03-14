from __future__ import annotations

import pandas as pd

from ogn_tool.reporting.network_engineering_report_builder import build_network_engineering_report



def test_network_engineering_report_builder_returns_all_sections() -> None:
    metrics = {
        'station_health': pd.DataFrame([
            {'station_id': 'S1', 'health_status': 'CRITICAL', 'impact_score': 5.0, 'influence_score': 3.5, 'anomaly_count': 1, 'primary_anomaly': 'critical_single_station', 'notes': 'x'},
        ]),
        'network_summary': {'network_status': 'DEGRADED'},
        'station_dependency': pd.DataFrame([
            {'station_id': 'S1', 'depends_on_station': 'S2', 'dependency_strength': 0.85, 'dependency_type': 'overlap_dominance', 'notes': 'x'},
        ]),
        'network_redundancy': {'redundancy_score': 0.22, 'interpretation': 'critical network'},
        'network_confidence': {'confidence_score': 0.45},
        'station_dominance': pd.DataFrame([
            {'station_id': 'S1', 'total_aircraft_count': 10, 'unique_aircraft_count': 8, 'shared_aircraft_count': 2, 'dominance_ratio': 0.8, 'dominance_rank': 1},
        ]),
    }
    spatial_observations = pd.DataFrame([{'station_id': 'S1', 'lat': 47.0, 'lon': 7.0}])

    report = build_network_engineering_report(metrics, spatial_observations)

    assert report.network_summary == {'network_status': 'DEGRADED'}
    assert not report.station_health_table.empty
    assert report.network_redundancy['redundancy_score'] == 0.22
    assert report.network_confidence['confidence_score'] == 0.45
    assert not report.station_dependency.empty
    assert not report.station_dominance.empty
    assert not report.spatial_observations.empty
    assert report.recommended_actions



def test_network_engineering_report_builder_propagates_metric_tables() -> None:
    station_health = pd.DataFrame([{'station_id': 'S1', 'health_status': 'GOOD'}])
    station_dependency = pd.DataFrame([{'station_id': 'S1', 'depends_on_station': 'S2', 'dependency_strength': 0.2}])
    station_dominance = pd.DataFrame([{'station_id': 'S1', 'dominance_ratio': 0.1}])
    spatial_observations = pd.DataFrame([{'station_id': 'S1', 'lat': 47.0, 'lon': 7.0}])
    metrics = {
        'station_health': station_health,
        'network_summary': {'network_status': 'GOOD'},
        'station_dependency': station_dependency,
        'network_redundancy': {'redundancy_score': 0.9},
        'network_confidence': {'confidence_score': 0.9},
        'station_dominance': station_dominance,
    }

    report = build_network_engineering_report(metrics, spatial_observations)

    assert report.station_health_table.equals(station_health)
    assert report.station_dependency.equals(station_dependency)
    assert report.station_dominance.equals(station_dominance)
    assert report.spatial_observations.equals(spatial_observations)
