from __future__ import annotations

import pandas as pd

from ogn_tool.models.rf_analysis_results import RFAnalysisResults
from ogn_tool.reporting import NetworkEngineeringReport, build_network_engineering_report


def test_build_network_engineering_report_from_typed_metrics() -> None:
    results = RFAnalysisResults(
        network_metrics={
            "network_summary": {
                "network_status": "WARNING",
                "notes": ["Coverage gap detected north-east valley"],
            },
            "station_health": pd.DataFrame(
                [
                    {"station_id": "S1", "health_status": "CRITICAL", "impact_score": 0.8},
                    {"station_id": "S2", "health_status": "WARNING", "impact_score": 0.4},
                ]
            ),
            "spof": pd.DataFrame(
                [
                    {
                        "station_id": "S1",
                        "spof_level": "HIGH",
                        "coverage_loss_ratio": 0.3,
                        "aircraft_lost": 15,
                        "spof_score": 4.5,
                    }
                ]
            ),
            "coverage_gaps": pd.DataFrame(
                [
                    {
                        "lat": 47.31,
                        "lon": 7.28,
                        "station_count": 1,
                        "gap_level": "HIGH",
                        "notes": "single station coverage",
                    }
                ]
            ),
            "station_redundancy_planner": pd.DataFrame(
                [
                    {
                        "target_station": "S1",
                        "coverage_loss": 0.3,
                        "aircraft_lost": 15,
                        "priority": 4.5,
                        "notes": "high removal impact",
                    }
                ]
            ),
            "station_addition_simulation": pd.DataFrame(
                [
                    {
                        "lat": 47.32,
                        "lon": 7.27,
                        "coverage_gain": 6,
                        "redundancy_gain": 3,
                        "priority_score": 15,
                        "notes": "empirical station addition simulation",
                    }
                ]
            ),
        }
    )

    report = build_network_engineering_report(results)

    assert isinstance(report, NetworkEngineeringReport)
    assert report.network_status == "WARNING"
    assert report.critical_stations == ["S1"]
    assert report.warning_stations == ["S2"]
    assert report.top_spof_stations[0]["station_id"] == "S1"
    assert report.top_gap_candidates[0]["gap_level"] == "HIGH"
    assert report.top_redundancy_priorities[0]["target_station"] == "S1"
    assert report.top_station_addition_candidates[0]["priority_score"] == 15
    assert report.summary_notes == ["Coverage gap detected north-east valley"]
