from ogn_tool.engine.rf_engine import RFAnalysisEngine
import pandas as pd


def test_rf_dataset_schema():
    # minimal empty dataset
    df = pd.DataFrame()

    engine = RFAnalysisEngine(
        df,
        station_lat=47.33,
        station_lon=7.27,
    )

    dataset = engine.build_analysis_dataset()

    required_keys = [
        "observations",
        "coverage_grid",
        "azimuth_histogram",
        "directional_balance",
        "station_metrics",
        "network_metrics",
        "shadow_map",
        "network_blind_zones",
    ]

    for key in required_keys:
        assert key in dataset, f"Dataset missing key: {key}"

    optional_keys = [
        "rf_diagnosis",
        "station_overlap_matrix",
        "station_recommendations",
    ]

    for key in optional_keys:
        if key in dataset:
            assert dataset[key] is not None
