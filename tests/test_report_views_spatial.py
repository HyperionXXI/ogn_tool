from ogn_tool.reporting.report_views import build_report_view, build_spatial_view


def _codes(diags):
    return {d.get("code") for d in diags if isinstance(d, dict)}


def test_full_report_embeds_spatial_view():
    report = {
        "network_metrics": {
            "network_graph": {
                "nodes": [{"id": "S1", "type": "station", "lat": 47.0, "lon": 7.0}],
                "edges": [{"source": "S1", "target": "A1"}],
            }
        },
        "coverage": [{"lat": 47.0, "lon": 7.0, "intensity": 0.9}],
    }

    view = build_report_view(report)

    assert "spatial" in view
    spatial = view["spatial"]
    assert spatial["stations"] == [{"id": "S1", "lat": 47.0, "lon": 7.0}]
    assert spatial["links"] == [{"src": "S1", "dst": "A1"}]
    assert spatial["coverage"] == [{"lat": 47.0, "lon": 7.0, "intensity": 0.9}]
    assert spatial["diagnostics"] == []


def test_missing_network_graph_propagates_diagnostics():
    report = {"coverage": [{"lat": 47.0, "lon": 7.0, "intensity": 1.0}]}

    spatial = build_spatial_view(report)
    codes = _codes(spatial["diagnostics"])

    assert spatial["stations"] == []
    assert spatial["links"] == []
    assert spatial["coverage"] == [{"lat": 47.0, "lon": 7.0, "intensity": 1.0}]
    assert "spatial_view.network_graph_missing" in codes
    assert "network_graph.nodes_missing" in codes
    assert "network_graph.edges_missing" in codes


def test_missing_coverage_propagates_diagnostics():
    report = {
        "network_graph": {
            "nodes": [{"id": "S1", "type": "station", "lat": 47.0, "lon": 7.0}],
            "edges": [{"source": "S1", "target": "A1"}],
        }
    }

    spatial = build_spatial_view(report)
    codes = _codes(spatial["diagnostics"])

    assert spatial["stations"] == [{"id": "S1", "lat": 47.0, "lon": 7.0}]
    assert spatial["links"] == [{"src": "S1", "dst": "A1"}]
    assert spatial["coverage"] == []
    assert "spatial_view.coverage_missing" in codes
    assert "coverage.missing" in codes


def test_invalid_report_safe_fallback():
    view = build_report_view("nope")  # type: ignore[arg-type]
    assert "spatial" in view
    spatial = view["spatial"]
    assert spatial["stations"] == []
    assert spatial["links"] == []
    assert spatial["coverage"] == []
    assert _codes(spatial["diagnostics"]) == {"spatial_view.invalid_report_type"}

