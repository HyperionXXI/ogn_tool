from __future__ import annotations

import pandas as pd
import pytest

from ogn_tool.runtime.coverage_gap_detection import detect_coverage_gaps


def test_detect_coverage_gaps_requires_dataframe() -> None:
    with pytest.raises(ValueError):
        detect_coverage_gaps(None)


def test_detect_coverage_gaps_requires_lat_lon_columns() -> None:
    observations = pd.DataFrame([{"lat": 47.3}])

    with pytest.raises(ValueError):
        detect_coverage_gaps(observations)


def test_detect_coverage_gaps_groups_points_and_filters_by_threshold() -> None:
    observations = pd.DataFrame(
        [
            {"lat": 47.301, "lon": 7.281},
            {"lat": 47.304, "lon": 7.284},
            {"lat": 47.309, "lon": 7.289},
            {"lat": 47.351, "lon": 7.101},
        ]
    )

    gaps = detect_coverage_gaps(observations, min_points=2, grid_size=0.02)

    assert gaps == [
        {"lat": 47.36, "lon": 7.1000000000000005, "observation_count": 1}
    ]


def test_detect_coverage_gaps_drops_invalid_rows() -> None:
    observations = pd.DataFrame(
        [
            {"lat": 47.301, "lon": 7.281},
            {"lat": "bad", "lon": 7.282},
            {"lat": 47.350, "lon": None},
        ]
    )

    gaps = detect_coverage_gaps(observations, min_points=1, grid_size=0.02)

    assert gaps == [
        {"lat": 47.300000000000004, "lon": 7.28, "observation_count": 1}
    ]
