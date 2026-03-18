from ogn_tool.reporting.run_comparison_views import build_run_comparison_view


def _has_diag_code(view: dict, code: str) -> bool:
    diags = view.get("diagnostics") or []
    return any(isinstance(d, dict) and d.get("code") == code for d in diags)


def test_identical_reports_zero_delta():
    report = {
        "network_metrics": {
            "network_summary": {"network_status": "OK", "critical_station_count": 0, "warning_station_count": 0},
            "network_graph": {
                "nodes": [
                    {"id": "S1", "type": "station", "lat": 47.0, "lon": 7.0},
                    {"id": "S2", "type": "station", "lat": 48.0, "lon": 8.0},
                ],
                "edges": [{"source": "S1", "target": "A1"}],
            },
        },
        "coverage": [
            {"lat": 47.0, "lon": 7.0, "intensity": 0.9},
            {"lat": 47.1, "lon": 7.1, "intensity": 0.2},
        ],
        "summary_metrics": {},
    }

    view = build_run_comparison_view(report, report)

    assert view["spatial_delta"]["station_count"]["delta"] == 0
    assert view["spatial_delta"]["link_count"]["delta"] == 0
    assert view["spatial_delta"]["coverage_point_count"]["delta"] == 0
    assert view["topology_delta"]["station_count"]["delta"] == 0
    assert view["topology_delta"]["link_count"]["delta"] == 0
    assert view["summary_delta"]["critical_station_count"]["delta"] == 0
    assert view["summary_delta"]["warning_station_count"]["delta"] == 0
    assert view["summary_delta"]["network_status"]["changed"] is False
    assert isinstance(view["diagnostics"], list)


def test_missing_sections_sets_comparability_flags():
    report_a = {}
    report_b = {"coverage": [{"lat": 47.0, "lon": 7.0, "intensity": 1.0}]}

    view = build_run_comparison_view(report_a, report_b)

    assert view["comparability"]["spatial"]["has_network_graph_a"] is False
    assert view["comparability"]["spatial"]["has_network_graph_b"] is False
    assert view["comparability"]["spatial"]["has_coverage_a"] is False
    assert view["comparability"]["spatial"]["has_coverage_b"] is True
    assert view["comparability"]["spatial"]["comparable"] is False
    assert isinstance(view["diagnostics"], list)


def test_different_spatial_detects_delta():
    report_a = {
        "network_metrics": {
            "network_graph": {
                "nodes": [{"id": "S1", "type": "station", "lat": 47.0, "lon": 7.0}],
                "edges": [],
            }
        },
        "coverage": [{"lat": 47.0, "lon": 7.0, "intensity": 0.5}],
    }
    report_b = {
        "network_metrics": {
            "network_graph": {
                "nodes": [
                    {"id": "S1", "type": "station", "lat": 47.0, "lon": 7.0},
                    {"id": "S2", "type": "station", "lat": 48.0, "lon": 8.0},
                ],
                "edges": [{"source": "S1", "target": "A1"}],
            }
        },
        "coverage": [
            {"lat": 47.0, "lon": 7.0, "intensity": 0.5},
            {"lat": 47.1, "lon": 7.1, "intensity": 0.2},
        ],
    }

    view = build_run_comparison_view(report_a, report_b)

    assert view["spatial_delta"]["station_count"]["delta"] == 1
    assert view["spatial_delta"]["link_count"]["delta"] == 1
    assert view["spatial_delta"]["coverage_point_count"]["delta"] == 1
    assert isinstance(view["diagnostics"], list)
