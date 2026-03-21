from ogn_tool.domain.rf_analysis import (
    build_feature_matrix as _build_feature_matrix,
    build_rf_probability_field as _build_rf_probability_field,
    detect_network_blind_zones as _detect_network_blind_zones,
    detect_shadow_sectors as _detect_shadow_sectors,
    estimate_antenna_pattern as _estimate_antenna_pattern,
    evaluate_rf_diagnosis as _evaluate_rf_diagnosis,
    station_quality_module as _station_quality_module,
    station_range_module as _station_range_module,
    summarize_signal_quality as _summarize_signal_quality,
)


def build_feature_matrix(observations):
    return _build_feature_matrix(observations)


def build_rf_probability_grid(df_packets):
    return _build_rf_probability_field(df_packets)


def compute_network_blind_zones(df, grid_size_km: float = 5):
    return _detect_network_blind_zones(df, grid_size_km=grid_size_km)


def compute_station_range(df):
    return _station_range_module.analyze(df)


def compute_station_quality(df):
    return _station_quality_module.analyze(df)


def estimate_antenna_pattern(feature_matrix, bins: int = 36):
    return _estimate_antenna_pattern(feature_matrix, bins=bins)


def detect_shadow_sectors(pattern, threshold: float = 0.4):
    return _detect_shadow_sectors(pattern, threshold=threshold)


def evaluate_rf_diagnosis(metrics, directional_balance):
    return _evaluate_rf_diagnosis(metrics, directional_balance)


def aggregate_signal_quality(df):
    return _summarize_signal_quality(df)


# Backward-compatible aliases used by existing callers outside engine.
analysis_station_quality = _station_quality_module
analysis_station_range = _station_range_module
build_rf_probability_field = _build_rf_probability_field
detect_network_blind_zones = _detect_network_blind_zones

__all__ = [
    "aggregate_signal_quality",
    "analysis_station_quality",
    "analysis_station_range",
    "build_feature_matrix",
    "build_rf_probability_field",
    "build_rf_probability_grid",
    "compute_network_blind_zones",
    "compute_station_quality",
    "compute_station_range",
    "detect_network_blind_zones",
    "detect_shadow_sectors",
    "evaluate_rf_diagnosis",
    "estimate_antenna_pattern",
]
