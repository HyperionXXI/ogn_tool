from __future__ import annotations

from ogn_tool.intelligence.spatial.analysis_anomaly_detection import detect_analysis_anomalies


def test_detect_analysis_anomalies_empty_diff() -> None:
    assert detect_analysis_anomalies({}) == []


def test_detect_analysis_anomalies_network_status_change() -> None:
    diff = {
        "metric_diffs": {
            "network_summary": {
                "network_status": {"changed": True}
            }
        }
    }

    assert detect_analysis_anomalies(diff) == ["network status changed"]


def test_detect_analysis_anomalies_fragility_increase() -> None:
    diff = {
        "metric_diffs": {
            "network_summary": {
                "single_station_ratio": {"delta": 0.2}
            }
        }
    }

    assert detect_analysis_anomalies(diff) == ["network fragility increased"]


def test_detect_analysis_anomalies_new_spof() -> None:
    diff = {
        "metric_diffs": {
            "spof": {
                "station_count": {"delta": 1}
            }
        }
    }

    assert detect_analysis_anomalies(diff) == ["new SPOF stations detected"]


def test_detect_analysis_anomalies_new_coverage_gaps() -> None:
    diff = {
        "metric_diffs": {
            "coverage_gaps": {
                "gap_count": {"delta": 2}
            }
        }
    }

    assert detect_analysis_anomalies(diff) == ["new coverage gaps detected"]


def test_detect_analysis_anomalies_combines_multiple_signals() -> None:
    diff = {
        "metric_diffs": {
            "network_summary": {
                "network_status": {"changed": True},
                "single_station_ratio": {"delta": 0.2},
            },
            "spof": {
                "station_count": {"delta": 1},
            },
            "coverage_gaps": {
                "gap_count": {"delta": 2},
            },
        }
    }

    assert detect_analysis_anomalies(diff) == [
        "network status changed",
        "network fragility increased",
        "new SPOF stations detected",
        "new coverage gaps detected",
    ]
