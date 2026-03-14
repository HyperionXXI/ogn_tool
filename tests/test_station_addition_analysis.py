from __future__ import annotations

import pandas as pd

from ogn_tool.runtime.station_addition_analysis import analyze_station_addition


def test_station_addition_analysis(monkeypatch) -> None:
    baseline_snapshot = {
        "analysis_run": {"run_id": "run_a"},
        "network_metrics": {
            "network_summary": {
                "network_status": "GOOD"
            }
        },
    }

    observations = pd.DataFrame(
        [
            {"lat": 47.0, "lon": 7.0, "station_id": "S1"},
        ]
    )

    def fake_simulate_station_addition(candidates, observations):
        return pd.DataFrame(
            [
                {
                    "aircraft_supported": 10,
                    "coverage_gain": 4,
                    "redundancy_gain": 2,
                    "priority_score": 6,
                }
            ]
        )

    monkeypatch.setattr(
        "ogn_tool.runtime.station_addition_analysis.simulate_station_addition",
        fake_simulate_station_addition,
    )

    result = analyze_station_addition(
        baseline_snapshot,
        observations=observations,
        lat=47.31,
        lon=7.28,
    )

    assert result["baseline_run_id"] == "run_a"
    assert result["scenario"] == "station_addition"
    assert result["candidate"] == {"lat": 47.31, "lon": 7.28}

    metrics = result["scenario_metrics"]
    assert metrics["aircraft_supported"] == 10
    assert metrics["coverage_gain"] == 4
    assert metrics["redundancy_gain"] == 2
    assert metrics["priority_score"] == 6

    assert "coverage improved" in result["anomalies"]
    assert "redundancy improved" in result["anomalies"]
    assert "high-priority candidate" in result["anomalies"]
