import pandas as pd
from ogn_tool.analysis.rf_metrics.blind_zone_detection import detect_rf_blind_zones


def test_blind_zone_detection():

    df = pd.DataFrame({
        "src": ["A1","A2","A3","A4"],
        "igate": ["S1","S1","S1","S1"],
        "lat": [47.0,47.01,47.02,47.03],
        "lon": [7.0,7.01,7.02,7.03],
        "ts_epoch":[1,2,3,4]
    })

    grid = detect_rf_blind_zones(df)

    assert "blind_score" in grid.columns

