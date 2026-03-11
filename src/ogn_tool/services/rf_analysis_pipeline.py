import pandas as pd

from ogn_tool.analysis.rf_visibility_model import compute_expected_vs_observed_range
from ogn_tool.analysis.station_placement_optimizer import find_candidate_station_locations
from ogn_tool.analysis.rf_blind_zone_detection import detect_rf_blind_zones


def run_rf_analysis(df: pd.DataFrame):

    results = {}

    if df is None or len(df) == 0:
        return results

    # Visibility model
    results["visibility"] = compute_expected_vs_observed_range(df)

    # Blind zones
    results["blind_zones"] = detect_rf_blind_zones(df)

    # Station optimizer
    results["station_candidates"] = find_candidate_station_locations(df)

    return results
