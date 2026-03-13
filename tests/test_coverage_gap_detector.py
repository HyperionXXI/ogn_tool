import pandas as pd
import pytest

from ogn_tool.analysis.intelligence.coverage_gap_detector import detect_coverage_gaps


def test_detect_coverage_gaps_basic():
    observations = pd.DataFrame(
        {
            "lat": [47.30, 47.30, 47.30, 47.31],
            "lon": [7.30, 7.30, 7.30, 7.31],
            "station_id": ["A", "B", "A", "C"],
        }
    )

    result = detect_coverage_gaps(
        observations,
        min_station_count=2,
        grid_resolution=0.01,
    )

    assert len(result) == 2
    cell = result[result["station_count"] == 2].iloc[0]
    assert cell["gap_level"] == "MEDIUM"
    cell = result[result["station_count"] == 1].iloc[0]
    assert cell["gap_level"] == "HIGH"


def test_detect_coverage_gaps_requires_columns():
    observations = pd.DataFrame({"lat": [47.3], "lon": [7.3]})
    with pytest.raises(ValueError, match="Missing required columns"):
        detect_coverage_gaps(observations)
