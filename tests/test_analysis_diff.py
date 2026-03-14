from __future__ import annotations

from ogn_tool.runtime.analysis_diff import diff_snapshots


def test_diff_snapshots_handles_empty_inputs() -> None:
    diff = diff_snapshots({}, {})

    assert diff["baseline_run_id"] is None
    assert diff["current_run_id"] is None
    assert diff["metric_diffs"]["network_summary"] == {}
    assert diff["metric_diffs"]["spof"]["station_count"]["baseline"] == 0
    assert diff["metric_diffs"]["coverage_gaps"]["gap_count"]["current"] == 0


def test_diff_snapshots_tracks_scalar_network_summary_change() -> None:
    baseline = {
        "analysis_run": {"run_id": "run_a"},
        "network_metrics": {
            "network_summary": {
                "network_status": "GOOD",
                "single_station_ratio": 0.10,
            }
        },
    }
    current = {
        "analysis_run": {"run_id": "run_b"},
        "network_metrics": {
            "network_summary": {
                "network_status": "WARNING",
                "single_station_ratio": 0.25,
            }
        },
    }

    diff = diff_snapshots(baseline, current)

    assert diff["baseline_run_id"] == "run_a"
    assert diff["current_run_id"] == "run_b"
    assert diff["metric_diffs"]["network_summary"]["single_station_ratio"]["delta"] == 0.15
    assert diff["metric_diffs"]["network_summary"]["network_status"]["changed"] is True


def test_diff_snapshots_tracks_spof_station_changes() -> None:
    baseline = {
        "network_metrics": {
            "spof": [
                {"station_id": "S1", "spof_score": 4.0},
                {"station_id": "S2", "spof_score": 3.0},
            ]
        }
    }
    current = {
        "network_metrics": {
            "spof": [
                {"station_id": "S2", "spof_score": 3.5},
                {"station_id": "S3", "spof_score": 5.0},
            ]
        }
    }

    diff = diff_snapshots(baseline, current)

    assert diff["metric_diffs"]["spof"]["station_count"]["delta"] == 0
    assert diff["metric_diffs"]["spof"]["stations_added"] == ["S3"]
    assert diff["metric_diffs"]["spof"]["stations_removed"] == ["S1"]


def test_diff_snapshots_tracks_coverage_gap_count_and_set_changes() -> None:
    baseline = {
        "network_metrics": {
            "coverage_gaps": [
                {"lat": 47.1, "lon": 7.1, "gap_level": "HIGH"},
            ]
        }
    }
    current = {
        "network_metrics": {
            "coverage_gaps": [
                {"lat": 47.1, "lon": 7.1, "gap_level": "HIGH"},
                {"lat": 47.2, "lon": 7.2, "gap_level": "CRITICAL"},
            ]
        }
    }

    diff = diff_snapshots(baseline, current)

    assert diff["metric_diffs"]["coverage_gaps"]["gap_count"]["delta"] == 1
    assert diff["metric_diffs"]["coverage_gaps"]["gaps_added"] == [(47.2, 7.2)]
    assert diff["metric_diffs"]["coverage_gaps"]["gaps_removed"] == []


def test_diff_snapshots_handles_missing_metrics() -> None:
    baseline = {"network_metrics": {}}
    current = {"network_metrics": {"network_summary": {"station_count": 4}}}

    diff = diff_snapshots(baseline, current)

    assert diff["metric_diffs"]["network_summary"]["station_count"]["baseline"] is None
    assert diff["metric_diffs"]["network_summary"]["station_count"]["current"] == 4
    assert diff["metric_diffs"]["spof"]["stations_added"] == []
    assert diff["metric_diffs"]["coverage_gaps"]["gaps_removed"] == []
