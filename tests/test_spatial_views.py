import pandas as pd

from ogn_tool.reporting.spatial_views import build_spatial_view


def _diag_codes(diags):
    return {d.get("code") for d in diags if isinstance(d, dict)}


def test_build_spatial_view_valid_report():
    report = {
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
            {"lat": 47.0, "lon": 7.0, "intensity": 0.8},
            {"lat": 47.1, "lon": 7.1, "intensity": 0.4},
        ],
    }

    out = build_spatial_view(report)

    assert out["stations"] == [
        {"id": "S1", "lat": 47.0, "lon": 7.0},
        {"id": "S2", "lat": 48.0, "lon": 8.0},
    ]
    assert out["links"] == [{"src": "S1", "dst": "A1"}]
    assert out["coverage"] == [
        {"lat": 47.0, "lon": 7.0, "intensity": 0.8},
        {"lat": 47.1, "lon": 7.1, "intensity": 0.4},
    ]
    assert out["diagnostics"] == []


def test_build_spatial_view_missing_network_graph():
    report = {
        "coverage": [{"lat": 47.0, "lon": 7.0, "intensity": 1.0}],
    }

    out = build_spatial_view(report)

    assert out["stations"] == []
    assert out["links"] == []
    assert out["coverage"] == [{"lat": 47.0, "lon": 7.0, "intensity": 1.0}]

    codes = _diag_codes(out["diagnostics"])
    assert "spatial_view.network_graph_missing" in codes
    # propagated from spatial_builder
    assert "network_graph.nodes_missing" in codes
    assert "network_graph.edges_missing" in codes


def test_build_spatial_view_missing_coverage():
    report = {
        "network_graph": {
            "nodes": [{"id": "S1", "type": "station", "lat": 47.0, "lon": 7.0}],
            "edges": [{"source": "S1", "target": "A1"}],
        }
    }

    out = build_spatial_view(report)

    assert out["stations"] == [{"id": "S1", "lat": 47.0, "lon": 7.0}]
    assert out["links"] == [{"src": "S1", "dst": "A1"}]
    assert out["coverage"] == []

    codes = _diag_codes(out["diagnostics"])
    assert "spatial_view.coverage_missing" in codes
    # propagated from spatial_builder
    assert "coverage.missing" in codes


def test_build_spatial_view_empty_report():
    out = build_spatial_view({})

    assert out["stations"] == []
    assert out["links"] == []
    assert out["coverage"] == []

    codes = _diag_codes(out["diagnostics"])
    assert "spatial_view.network_graph_missing" in codes
    assert "spatial_view.coverage_missing" in codes
    assert "network_graph.nodes_missing" in codes
    assert "network_graph.edges_missing" in codes
    assert "coverage.missing" in codes


def test_build_spatial_view_invalid_report_type():
    out = build_spatial_view("nope")  # type: ignore[arg-type]
    assert out["stations"] == []
    assert out["links"] == []
    assert out["coverage"] == []
    assert _diag_codes(out["diagnostics"]) == {"spatial_view.invalid_report_type"}


def test_build_spatial_view_invalid_coverage_type():
    report = {
        "network_graph": {
            "nodes": [{"id": "S1", "type": "station", "lat": 47.0, "lon": 7.0}],
            "edges": [{"source": "S1", "target": "A1"}],
        },
        "coverage": "not-a-list",
    }

    out = build_spatial_view(report)

    assert out["stations"] == [{"id": "S1", "lat": 47.0, "lon": 7.0}]
    assert out["links"] == [{"src": "S1", "dst": "A1"}]
    assert out["coverage"] == []

    codes = _diag_codes(out["diagnostics"])
    assert "spatial_view.coverage_missing" in codes
    assert "coverage.missing" in codes


def test_build_spatial_view_coverage_missing_columns():
    report = {
        "network_graph": {
            "nodes": [{"id": "S1", "type": "station", "lat": 47.0, "lon": 7.0}],
            "edges": [],
        },
        "coverage": [{"lat": 47.0, "lon": 7.0}],  # missing intensity
    }

    out = build_spatial_view(report)
    assert out["coverage"] == []

    codes = _diag_codes(out["diagnostics"])
    assert "coverage.missing_columns" in codes

