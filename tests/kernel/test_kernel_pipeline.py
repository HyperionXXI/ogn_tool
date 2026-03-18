import pandas as pd

from ogn_tool.engine.multi_station_intelligence_facade import (
    build_candidate_station_aircraft_sets,
    build_station_addition_evaluations,
    evaluate_multi_station_coverage,
    select_stations_lazy_greedy,
)
from ogn_tool.engine.network_graph_analysis_facade import (
    compute_temporal_observability,
    network_confidence_level,
    network_redundancy_level,
)
from ogn_tool.engine.rf_analysis_facade import (
    build_feature_matrix,
    build_rf_probability_grid,
    compute_network_blind_zones,
    detect_shadow_sectors,
    estimate_antenna_pattern,
)


def test_kernel_pipeline_smoke() -> None:
    distance_df = pd.DataFrame(
        [
            {
                "lat": 47.35,
                "lon": 7.50,
                "distance_km": 8.0,
                "bearing_deg": 95.0,
                "altitude_m": 1200.0,
                "radio_horizon_km": 140.0,
                "src": "ac1",
            },
            {
                "lat": 47.36,
                "lon": 7.54,
                "distance_km": 16.0,
                "bearing_deg": 110.0,
                "altitude_m": 1350.0,
                "radio_horizon_km": 150.0,
                "src": "ac2",
            },
        ]
    )

    feature_matrix = build_feature_matrix({"distance_df": distance_df})
    pattern = estimate_antenna_pattern(feature_matrix)
    probability_grid = build_rf_probability_grid(distance_df)
    blind_zones = compute_network_blind_zones(probability_grid)

    candidates = pd.DataFrame([
        {"candidate_id": "cand_a", "lat": 47.35, "lon": 7.50},
        {"candidate_id": "cand_b", "lat": 47.37, "lon": 7.56},
    ])
    observations = pd.DataFrame([
        {"aircraft_id": "ac1", "station_id": "st1", "lat": 47.35, "lon": 7.50},
        {"aircraft_id": "ac2", "station_id": "st1", "lat": 47.36, "lon": 7.55},
    ])

    station_aircraft = build_candidate_station_aircraft_sets(candidates, observations)
    coverage = evaluate_multi_station_coverage(station_aircraft)
    selected, covered = select_stations_lazy_greedy(station_aircraft, k=1)
    evaluations = build_station_addition_evaluations(candidates, observations)

    ts = pd.Series([1700000000, 1700003600, 1700007200])
    temporal = compute_temporal_observability(ts, 4)
    metrics = {
        "network_confidence": {"confidence_score": 0.8},
        "network_redundancy": {"redundancy_score": 0.6},
    }

    assert feature_matrix.packet_count == 2
    shadow_sectors = detect_shadow_sectors(pattern)
    assert isinstance(pattern, dict)
    assert "azimuth" in pattern
    assert "probability" in pattern
    assert isinstance(shadow_sectors, list)
    assert isinstance(blind_zones, pd.DataFrame)
    assert isinstance(coverage.unique_aircraft_supported, int)
    assert isinstance(selected, list)
    assert isinstance(covered, set)
    assert isinstance(evaluations, list)
    assert temporal.packet_count == 3
    assert network_confidence_level(metrics) == "good"
    assert network_redundancy_level(metrics) == "moderate"
