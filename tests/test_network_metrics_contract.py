from ogn_tool.reporting.contracts.network_metrics_contract import collect_network_metric_warnings


def test_collect_network_metric_warnings_reports_missing_families() -> None:
    metrics = {
        "network_summary": {},
        "visibility": {},
    }

    warnings = collect_network_metric_warnings(metrics)

    assert "network_redundancy not produced by analysis pipeline" in warnings
    assert "shadow_risk_scores not produced by analysis pipeline" in warnings
