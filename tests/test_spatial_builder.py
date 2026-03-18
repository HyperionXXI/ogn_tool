import pandas as pd

from ogn_tool.reporting.spatial_builder import (
    extract_coverage_points,
    extract_links_from_graph,
    extract_stations_from_graph,
)


def _diag_codes(diags):
    return {d.get("code") for d in diags if isinstance(d, dict)}


def test_extract_stations_from_graph_valid_input():
    graph = {
        "nodes": [
            {"id": "S1", "type": "station", "lat": 47.0, "lon": 7.0},
            {"id": "S2", "type": "station", "lat": 48.0, "lon": 8.0},
            # Non-station nodes are ignored in strict extraction
            {"id": "A1", "type": "aircraft", "lat": 46.0, "lon": 6.0},
        ],
        "edges": [],
    }

    stations, diags = extract_stations_from_graph(graph)

    assert stations == [
        {"id": "S1", "lat": 47.0, "lon": 7.0},
        {"id": "S2", "lat": 48.0, "lon": 8.0},
    ]
    # No "no_station_nodes" warning when valid stations exist
    assert "network_graph.no_station_nodes" not in _diag_codes(diags)


def test_extract_stations_from_graph_missing_fields():
    graph = {
        "nodes": [
            {"id": "S1", "type": "station", "lat": 47.0},  # missing lon
            {"type": "station", "lat": 48.0, "lon": 8.0},  # missing id
        ],
        "edges": [],
    }

    stations, diags = extract_stations_from_graph(graph)

    assert stations == []
    codes = _diag_codes(diags)
    assert "network_graph.node_missing_fields" in codes
    assert "network_graph.no_station_nodes" in codes

    # Ensure missing field list is present and meaningful
    missing_lists = [d.get("missing") for d in diags if d.get("code") == "network_graph.node_missing_fields"]
    assert any(isinstance(m, list) and m for m in missing_lists)


def test_extract_stations_from_graph_invalid_types():
    graph = {"nodes": "not-a-list", "edges": []}

    stations, diags = extract_stations_from_graph(graph)

    assert stations == []
    assert _diag_codes(diags) == {"network_graph.nodes_missing"}
    assert diags[0]["source"] == "network_graph"
    assert "nodes" in diags[0]["missing"]


def test_extract_stations_from_graph_empty_data():
    graph = {"nodes": [], "edges": []}

    stations, diags = extract_stations_from_graph(graph)

    assert stations == []
    assert "network_graph.no_station_nodes" in _diag_codes(diags)


def test_extract_links_from_graph_valid_input():
    graph = {
        "nodes": [],
        "edges": [
            {"source": "S1", "target": "A1"},
            {"source": "S1", "target": "A2"},
        ],
    }

    links, diags = extract_links_from_graph(graph)

    assert links == [{"src": "S1", "dst": "A1"}, {"src": "S1", "dst": "A2"}]
    assert "network_graph.no_edges" not in _diag_codes(diags)


def test_extract_links_from_graph_missing_fields():
    graph = {
        "nodes": [],
        "edges": [
            {"source": "S1"},  # missing target
            {"target": "A2"},  # missing source
        ],
    }

    links, diags = extract_links_from_graph(graph)

    assert links == []
    codes = _diag_codes(diags)
    assert "network_graph.edge_missing_fields" in codes
    assert "network_graph.no_edges" in codes


def test_extract_links_from_graph_invalid_types():
    graph = {"nodes": [], "edges": "not-a-list"}

    links, diags = extract_links_from_graph(graph)

    assert links == []
    assert _diag_codes(diags) == {"network_graph.edges_missing"}
    assert diags[0]["source"] == "network_graph"
    assert "edges" in diags[0]["missing"]


def test_extract_links_from_graph_empty_data():
    graph = {"nodes": [], "edges": []}

    links, diags = extract_links_from_graph(graph)

    assert links == []
    assert "network_graph.no_edges" in _diag_codes(diags)


def test_extract_coverage_points_valid_input():
    results_map = {
        "coverage": pd.DataFrame(
            [
                {"lat": 47.0, "lon": 7.0, "intensity": 0.8},
                {"lat": 47.1, "lon": 7.1, "intensity": 0.4},
            ]
        )
    }

    points, diags = extract_coverage_points(results_map)

    assert points == [
        {"lat": 47.0, "lon": 7.0, "intensity": 0.8},
        {"lat": 47.1, "lon": 7.1, "intensity": 0.4},
    ]
    # In valid case, no diagnostics are required
    assert diags == []


def test_extract_coverage_points_missing_fields():
    # Missing required column: intensity
    results_map = {"coverage": pd.DataFrame([{"lat": 47.0, "lon": 7.0}])}

    points, diags = extract_coverage_points(results_map)

    assert points == []
    assert _diag_codes(diags) == {"coverage.missing_columns"}
    assert diags[0]["missing"] == ["intensity"]
    assert diags[0]["source"] == "coverage"


def test_extract_coverage_points_invalid_types():
    results_map = {"coverage": "not-a-dataframe"}

    points, diags = extract_coverage_points(results_map)

    assert points == []
    assert _diag_codes(diags) == {"coverage.invalid_type"}
    assert diags[0]["source"] == "coverage"


def test_extract_coverage_points_empty_data():
    results_map = {"coverage": pd.DataFrame(columns=["lat", "lon", "intensity"])}

    points, diags = extract_coverage_points(results_map)

    assert points == []
    assert _diag_codes(diags) == {"coverage.empty"}
    assert diags[0]["source"] == "coverage"

