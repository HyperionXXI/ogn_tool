from ogn_tool.runtime.station_removal_analysis import analyze_station_removal


def test_station_removal_analysis_basic(monkeypatch):
    baseline_snapshot = {
        "analysis_run": {"run_id": "run_a"},
        "network_metrics": {
            "network_summary": {
                "network_status": "GOOD"
            }
        },
    }

    def fake_simulate_station_removal(*, station_id, network_metrics):
        return {
            "network_status_after_removal": "WARNING",
            "aircraft_lost": 5,
            "coverage_loss_ratio": 0.2,
            "stations_becoming_critical": ["S2"],
        }

    monkeypatch.setattr(
        "ogn_tool.runtime.station_removal_analysis.simulate_station_removal",
        fake_simulate_station_removal,
    )

    result = analyze_station_removal(
        baseline_snapshot,
        station_id="S1",
    )

    assert result["station_id"] == "S1"
    assert result["baseline_run_id"] == "run_a"
    assert result["scenario"] == "station_removal"

    metrics = result["scenario_metrics"]

    assert metrics["network_status_after_removal"] == "WARNING"
    assert metrics["coverage_loss_ratio"] == 0.2
    assert metrics["stations_becoming_critical"] == ["S2"]

    assert "network status changed" in result["anomalies"]
    assert "coverage loss increased" in result["anomalies"]
    assert "new critical stations detected" in result["anomalies"]
