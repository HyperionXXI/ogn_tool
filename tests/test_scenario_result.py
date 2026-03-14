from ogn_tool.models.scenario_result import ScenarioMetrics, ScenarioResult


def test_scenario_result_priority_score_uses_metrics() -> None:
    result = ScenarioResult(
        baseline_run_id="run_a",
        scenario="station_addition",
        metrics=ScenarioMetrics({"priority_score": 12}),
    )

    assert result.priority_score() == 12.0
    assert result.metrics["priority_score"] == 12
