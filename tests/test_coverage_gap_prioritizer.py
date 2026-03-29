import pandas as pd
import pytest

from ogn_tool.intelligence.coverage_gap_prioritizer import (
    prioritize_coverage_gaps,
)


def test_prioritize_coverage_gaps_basic():
    gaps = pd.DataFrame(
        {
            "lat": [47.30, 47.31, 47.32],
            "lon": [7.30, 7.31, 7.32],
            "station_count": [0, 1, 2],
            "gap_level": ["CRITICAL", "HIGH", "MEDIUM"],
            "notes": ["", "", ""],
        }
    )

    result = prioritize_coverage_gaps(gaps)

    assert not result.empty
    assert list(result.columns) == [
        "lat",
        "lon",
        "station_count",
        "gap_level",
        "priority_score",
        "recommended_action",
        "notes",
    ]
    assert result.iloc[0]["gap_level"] == "CRITICAL"
    assert result.iloc[0]["priority_score"] == 100


def test_prioritize_coverage_gaps_respects_max_candidates():
    gaps = pd.DataFrame(
        {
            "lat": [47.30, 47.31, 47.32],
            "lon": [7.30, 7.31, 7.32],
            "station_count": [0, 1, 2],
            "gap_level": ["CRITICAL", "HIGH", "MEDIUM"],
            "notes": ["", "", ""],
        }
    )

    result = prioritize_coverage_gaps(gaps, max_candidates=2)
    assert len(result) == 2


def test_prioritize_coverage_gaps_requires_columns():
    gaps = pd.DataFrame({"lat": [47.3], "lon": [7.3]})
    with pytest.raises(ValueError, match="Missing required columns"):
        prioritize_coverage_gaps(gaps)
