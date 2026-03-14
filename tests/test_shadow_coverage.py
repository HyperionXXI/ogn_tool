from __future__ import annotations

import pandas as pd

from ogn_tool.analysis.rf.shadow_coverage import (
    compute_shadow_risk_scores,
    compute_station_angular_entropy,
)



def test_uniform_distribution_entropy_high() -> None:
    df = pd.DataFrame(
        {
            "station_id": ["A"] * 4,
            "bearing_deg": [0, 90, 180, 270],
        }
    )

    entropy = compute_station_angular_entropy(df, sector_count=4)

    assert entropy["A"] > 0.9



def test_single_sector_entropy_low() -> None:
    df = pd.DataFrame(
        {
            "station_id": ["A"] * 10,
            "bearing_deg": [10] * 10,
        }
    )

    entropy = compute_station_angular_entropy(df, sector_count=16)

    assert entropy["A"] < 0.1



def test_shadow_risk_inverse_entropy() -> None:
    df = pd.DataFrame(
        {
            "station_id": ["A"] * 10,
            "bearing_deg": [15] * 10,
        }
    )

    risk = compute_shadow_risk_scores(df)

    assert risk["A"] > 0.8



def test_coordinate_based_bearing_input_supported() -> None:
    df = pd.DataFrame(
        {
            "station_id": ["A", "A"],
            "station_lat": [47.0, 47.0],
            "station_lon": [7.0, 7.0],
            "lat": [47.1, 47.0],
            "lon": [7.0, 7.1],
        }
    )

    entropy = compute_station_angular_entropy(df, sector_count=4)

    assert 0.0 <= entropy["A"] <= 1.0
