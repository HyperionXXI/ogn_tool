from ogn_tool.reporting.report_normalizer import build_ui_artifact


def _codes(diags):
    return {d.get("code") for d in diags if isinstance(d, dict)}


def test_report_complet_ok():
    report = {
        "network_graph": {
            "nodes": [
                {"id": "S1", "type": "station", "lat": 47.0, "lon": 7.0},
                {"id": "A1", "type": "aircraft", "lat": 47.1, "lon": 7.1, "altitude": 1200.0},
            ],
            "edges": [
                {"source": "S1", "target": "A1", "weight": 10.0, "type": "reception"},
            ],
        },
        "coverage": [{"lat": 47.0, "lon": 7.0, "intensity": 0.8}],
        "network_metrics": {
            "network_summary": {"network_status": "OK"},
            "station_health_table": [{"station_id": "S1", "health_status": "GOOD"}],
            "station_dependency": [{"station_id": "S1", "dependency_strength": 0.1}],
            "network_confidence": {"confidence_score": 0.9},
        },
        "input_warnings": [],
    }
    metadata = {
        "dataset": {"station_id": "S1"},
        "comparability": {"time_window_start": "2026-03-14T10:00:00Z", "time_window_end": "2026-03-14T11:00:00Z", "time_window_duration_s": 3600},
    }

    out = build_ui_artifact(report, metadata)

    assert out["meta"]["station_id"] == "S1"
    assert out["layers"]["stations"] == [{"id": "S1", "lat": 47.0, "lon": 7.0}]
    assert out["layers"]["aircraft"] == [{"id": "A1", "lat": 47.1, "lon": 7.1, "altitude": 1200.0}]
    assert out["layers"]["coverage"] == [{"lat": 47.0, "lon": 7.0, "intensity": 0.8}]
    assert out["layers"]["edges"] == [{"source": "S1", "target": "A1", "weight": 10.0, "type": "reception"}]
    assert out["network"]["summary"] == {"network_status": "OK"}
    assert out["network"]["health"] == [{"station_id": "S1", "health_status": "GOOD"}]
    assert out["network"]["dependency"] == [{"station_id": "S1", "dependency_strength": 0.1}]
    assert isinstance(out["diagnostics"], list)


def test_report_sans_coords_station_diagnostic():
    report = {
        "network_graph": {"nodes": [{"id": "S1", "type": "station"}], "edges": []},
        "coverage": [{"lat": 47.0, "lon": 7.0, "intensity": 0.8}],
        "network_metrics": {"network_confidence": {"confidence_score": 0.9}, "network_summary": {}},
        "input_warnings": [],
    }
    metadata = {"dataset": {"station_id": "S1"}, "comparability": {}}

    out = build_ui_artifact(report, metadata)
    assert out["layers"]["stations"] == []
    assert "station_missing_coordinates" in _codes(out["diagnostics"])


def test_report_sans_coverage_diagnostic():
    report = {
        "network_graph": {"nodes": [], "edges": []},
        "network_metrics": {"network_confidence": {"confidence_score": 0.9}, "network_summary": {}},
        "input_warnings": [],
    }
    metadata = {"dataset": {"station_id": "S1"}, "comparability": {}}

    out = build_ui_artifact(report, metadata)
    assert out["layers"]["coverage"] == []
    assert "missing_coverage" in _codes(out["diagnostics"])


def test_report_sans_network_metrics_diagnostic():
    report = {
        "network_graph": {"nodes": [], "edges": []},
        "coverage": [],
        "input_warnings": [],
    }
    metadata = {"dataset": {"station_id": "S1"}, "comparability": {}}

    out = build_ui_artifact(report, metadata)
    assert out["network"]["summary"] == {}
    assert "missing_network_metrics" in _codes(out["diagnostics"])

