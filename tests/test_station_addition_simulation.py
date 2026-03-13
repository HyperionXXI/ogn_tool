import pandas as pd
import pytest

from ogn_tool.analysis.intelligence.station_addition_simulation import (
    simulate_station_addition,
)


def test_station_addition_simulation_basic():
    observations = pd.DataFrame(
        {
            "lat": [47.30, 47.30, 47.31, 47.32],
            "lon": [7.30, 7.31, 7.30, 7.32],
            "station_id": ["A", "B", "A", "B"],
        }
    )

    candidates = pd.DataFrame(
        {
            "lat": [47.305],
            "lon": [7.305],
        }
    )

    result = simulate_station_addition(
        candidates,
        observations,
        grid_resolution=0.01,
    )

    assert len(result) == 1
    row = result.iloc[0]
    assert row["aircraft_supported"] >= 0
    assert row["priority_score"] >= 0


def test_station_addition_requires_columns():
    observations = pd.DataFrame({"lat": [47.3], "lon": [7.3]})
    candidates = pd.DataFrame({"lat": [47.3], "lon": [7.3]})

    with pytest.raises(ValueError, match="Missing observation columns"):
        simulate_station_addition(candidates, observations)
