from __future__ import annotations

import pandas as pd
import pytest

from ogn_tool.analysis.intelligence.station_redundancy_planner import (
    plan_redundancy_improvements,
)


def test_redundancy_planner_basic():
    matrix = pd.DataFrame(
        [
            {"src": "A1", "igate": "S1"},
            {"src": "A2", "igate": "S1"},
            {"src": "A2", "igate": "S2"},
            {"src": "A3", "igate": "S2"},
        ]
    )

    network_metrics = {"visibility": {"matrix": matrix}}

    result = plan_redundancy_improvements(network_metrics)

    assert not result.empty
    assert list(result.columns) == [
        "target_station",
        "coverage_loss",
        "aircraft_lost",
        "priority",
        "status_after_removal",
        "notes",
    ]
    assert result.iloc[0]["target_station"] == "S1"
    assert result.iloc[0]["priority"] >= result.iloc[-1]["priority"]


def test_redundancy_planner_empty_matrix_returns_empty_dataframe():
    result = plan_redundancy_improvements({"visibility": {"matrix": pd.DataFrame()}})
    assert result.empty


def test_redundancy_planner_requires_src_and_igate_columns():
    matrix = pd.DataFrame([{"aircraft_id": "A1", "station_id": "S1"}])

    with pytest.raises(ValueError, match="src, igate"):
        plan_redundancy_improvements({"visibility": {"matrix": matrix}})
