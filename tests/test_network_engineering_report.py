from __future__ import annotations

from ogn_tool.reporting.report_builder import build_network_engineering_report


class DummyResults:
    def __init__(self, metrics):
        self.network_metrics = metrics



def test_station_corridor_interpretation() -> None:
    results = DummyResults(
        {
            "station_angular_entropy": {"A": 0.1},
            "shadow_risk_scores": {"A": 0.9},
        }
    )

    report = build_network_engineering_report(results)

    assert "corridor" in report.station_diagnostics["A"].interpretation.lower()



def test_builder_accepts_dict_input() -> None:
    results = {
        "network_metrics": {
            "station_angular_entropy": {"A": 0.8},
            "shadow_risk_scores": {"A": 0.2},
        }
    }

    report = build_network_engineering_report(results)

    assert "robust" in report.station_diagnostics["A"].interpretation.lower()
