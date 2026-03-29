from __future__ import annotations

import pandas as pd
import pytest

from ogn_tool.intelligence.station_addition_evaluations import (
    build_station_addition_evaluations,
)
from ogn_tool.models.station_addition_evaluation import StationAdditionEvaluation



def test_build_station_addition_evaluations_returns_typed_rows(monkeypatch) -> None:
    def fake_simulate_station_addition(candidates, observations):
        return pd.DataFrame(
            [
                {
                    "lat": 47.31,
                    "lon": 7.28,
                    "aircraft_supported": 10,
                    "coverage_gain": 4,
                    "redundancy_gain": 2,
                    "priority_score": 6,
                }
            ]
        )

    monkeypatch.setattr(
        "ogn_tool.intelligence.station_addition_evaluations.simulate_station_addition",
        fake_simulate_station_addition,
    )

    evaluations = build_station_addition_evaluations(
        pd.DataFrame([{"lat": 47.31, "lon": 7.28}]),
        pd.DataFrame([{"lat": 47.0, "lon": 7.0, "station_id": "S1"}]),
    )

    assert evaluations == [
        StationAdditionEvaluation(
            candidate_id="cand_47.31000_7.28000",
            lat=47.31,
            lon=7.28,
            aircraft_supported=10,
            coverage_gain=4,
            redundancy_gain=2,
            priority_score=6,
        )
    ]



def test_build_station_addition_evaluations_reuses_candidate_id_when_present(monkeypatch) -> None:
    monkeypatch.setattr(
        "ogn_tool.intelligence.station_addition_evaluations.simulate_station_addition",
        lambda candidates, observations: pd.DataFrame(
            [{
                "lat": 47.31,
                "lon": 7.28,
                "aircraft_supported": 10,
                "coverage_gain": 4,
                "redundancy_gain": 2,
                "priority_score": 6,
            }]
        ),
    )

    evaluations = build_station_addition_evaluations(
        pd.DataFrame([{"candidate_id": "cand_fixed", "lat": 47.31, "lon": 7.28}]),
        pd.DataFrame([{"lat": 47.0, "lon": 7.0, "station_id": "S1"}]),
    )

    assert evaluations[0].candidate_id == "cand_fixed"



def test_build_station_addition_evaluations_raises_on_missing_output_columns(monkeypatch) -> None:
    def fake_simulate_station_addition(candidates, observations):
        return pd.DataFrame([{"lat": 47.31, "lon": 7.28, "coverage_gain": 4}])

    monkeypatch.setattr(
        "ogn_tool.intelligence.station_addition_evaluations.simulate_station_addition",
        fake_simulate_station_addition,
    )

    with pytest.raises(ValueError):
        build_station_addition_evaluations(
            pd.DataFrame([{"lat": 47.31, "lon": 7.28}]),
            pd.DataFrame([{"lat": 47.0, "lon": 7.0, "station_id": "S1"}]),
        )
