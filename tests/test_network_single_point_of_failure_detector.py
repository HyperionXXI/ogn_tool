from __future__ import annotations

import pandas as pd
import pytest

from ogn_tool.analysis.intelligence.network_single_point_of_failure_detector import (
    detect_single_points_of_failure,
)


def test_detect_spof_basic():
    matrix = pd.DataFrame(
        [
            {"src": "A1", "igate": "S1"},
            {"src": "A2", "igate": "S1"},
            {"src": "A2", "igate": "S2"},
            {"src": "A3", "igate": "S2"},
        ]
    )

    result = detect_single_points_of_failure({"visibility": {"matrix": matrix}})

    assert not result.empty
    assert list(result.columns) == [
        "station_id",
        "aircraft_lost",
        "coverage_loss_ratio",
        "spof_score",
        "network_status_after_removal",
        "spof_level",
        "notes",
    ]
    assert result.iloc[0]["station_id"] == "S1"
    assert result.iloc[0]["spof_level"] == "HIGH"
    assert result.iloc[0]["spof_score"] == result.iloc[0]["coverage_loss_ratio"] * result.iloc[0]["aircraft_lost"]


def test_detect_spof_empty_matrix_returns_empty_dataframe():
    result = detect_single_points_of_failure({"visibility": {"matrix": pd.DataFrame()}})
    assert result.empty


def test_detect_spof_requires_src_and_igate_columns():
    matrix = pd.DataFrame([{"aircraft_id": "A1", "station_id": "S1"}])

    with pytest.raises(ValueError, match="src, igate"):
        detect_single_points_of_failure({"visibility": {"matrix": matrix}})


def test_detect_spof_uses_spof_score_for_medium_classification():
    rows = []
    for idx in range(1, 22):
        rows.append({"src": f"L{idx}", "igate": "S1"})
    for idx in range(22, 86):
        rows.append({"src": f"S{idx}", "igate": "S1"})
        rows.append({"src": f"S{idx}", "igate": "S2"})

    matrix = pd.DataFrame(rows)
    result = detect_single_points_of_failure({"visibility": {"matrix": matrix}})
    row = result[result["station_id"] == "S1"].iloc[0]

    assert row["coverage_loss_ratio"] < 0.25
    assert row["spof_score"] >= 5.0
    assert row["spof_level"] == "MEDIUM"
