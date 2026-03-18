from ogn_tool.models.scenario_result import ScenarioMetrics, ScenarioResult
from ogn_tool.intelligence.network.network_robustness_analysis import analyze_network_robustness


def test_network_robustness_sorting(monkeypatch):
    def fake_analyze_station_removal(snapshot, *, station_id):
        data = {
            "S1": (0.20, ["A"]),
            "S2": (0.10, ["A", "B"]),
            "S3": (0.05, []),
        }

        loss, critical = data[station_id]

        return ScenarioResult(
            baseline_run_id="run",
            scenario="station_removal",
            station_id=station_id,
            metrics=ScenarioMetrics(
                {
                    "coverage_loss_ratio": loss,
                    "stations_becoming_critical": critical,
                }
            ),
            anomalies=[],
        )

    monkeypatch.setattr(
        "ogn_tool.intelligence.network.network_robustness_analysis.analyze_station_removal",
        fake_analyze_station_removal,
    )

    results = analyze_network_robustness(
        {},
        station_ids=["S1", "S2", "S3"],
    )

    assert [result.station_id for result in results] == ["S1", "S2", "S3"]


def test_network_robustness_ignores_invalid_station_ids(monkeypatch):
    def fake_analyze_station_removal(snapshot, *, station_id):
        return ScenarioResult(
            baseline_run_id="run",
            scenario="station_removal",
            station_id=station_id,
            metrics=ScenarioMetrics(
                {
                    "coverage_loss_ratio": 0.10,
                    "stations_becoming_critical": [],
                }
            ),
            anomalies=[],
        )

    monkeypatch.setattr(
        "ogn_tool.intelligence.network.network_robustness_analysis.analyze_station_removal",
        fake_analyze_station_removal,
    )

    results = analyze_network_robustness(
        {},
        station_ids=["S1", "", None, 42, "S2"],
    )

    assert [result.station_id for result in results] == ["S1", "S2"]
