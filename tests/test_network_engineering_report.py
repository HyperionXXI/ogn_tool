from __future__ import annotations

from ogn_tool.models.scenario_result import ScenarioMetrics, ScenarioResult
from ogn_tool.reporting.network_engineering_report import build_network_engineering_report
from ogn_tool.reporting.report_models import NetworkEngineeringReport


def test_build_network_engineering_report_with_all_inputs() -> None:
    report = build_network_engineering_report(
        network_metrics={
            "network_summary": {"network_status": "WARNING"},
            "station_health": [{"station_id": "S1", "health_score": 0.8}],
        },
        coverage_gaps=[{"lat": 47.3, "lon": 7.18, "observation_count": 1}],
        recommended_new_stations=[
            ScenarioResult(
                baseline_run_id="run_a",
                scenario="station_addition",
                candidate={"lat": 47.31, "lon": 7.28},
                metrics=ScenarioMetrics(
                    {
                        "priority_score": 34,
                        "coverage_gain": 12,
                        "redundancy_gain": 7,
                    }
                ),
                anomalies=[],
            )
        ],
        robustness_results=[
            ScenarioResult(
                baseline_run_id="run_a",
                scenario="station_removal",
                station_id="S9",
                metrics=ScenarioMetrics(
                    {
                        "coverage_loss_ratio": 0.18,
                        "stations_becoming_critical": ["S2"],
                    }
                ),
                anomalies=[],
            )
        ],
    )

    assert isinstance(report, NetworkEngineeringReport)
    assert report.network_status == "WARNING"
    assert report.station_health == [{"station_id": "S1", "health_score": 0.8}]
    assert report.coverage_gaps == [{"lat": 47.3, "lon": 7.18, "observation_count": 1}]
    assert report.critical_stations == [
        {
            "station_id": "S9",
            "candidate": None,
            "coverage_loss_ratio": 0.18,
            "stations_becoming_critical": ["S2"],
            "priority_score": None,
            "coverage_gain": None,
            "redundancy_gain": None,
        }
    ]
    assert report.recommended_new_stations == [
        {
            "station_id": None,
            "candidate": {"lat": 47.31, "lon": 7.28},
            "coverage_loss_ratio": None,
            "stations_becoming_critical": [],
            "priority_score": 34,
            "coverage_gain": 12,
            "redundancy_gain": 7,
        }
    ]


def test_build_network_engineering_report_handles_missing_optional_inputs() -> None:
    report = build_network_engineering_report(
        network_metrics={"network_summary": {"network_status": "GOOD"}},
    )

    assert report.network_status == "GOOD"
    assert report.station_health == []
    assert report.critical_stations == []
    assert report.coverage_gaps == []
    assert report.recommended_new_stations == []


def test_build_network_engineering_report_handles_empty_network_metrics() -> None:
    report = build_network_engineering_report(network_metrics={})

    assert report.network_status is None
    assert report.station_health == []
