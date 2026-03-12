import pandas as pd

from ogn_tool.analysis.network_graph import (
    build_coverage_graph,
    build_rf_graph,
    compute_graph_metrics,
    compute_station_aircraft_links,
)


def test_station_aircraft_links_and_coverage_graph():
    df = pd.DataFrame(
        {
            "station_id": ["S1", "S1", "S2"],
            "aircraft_id": ["A1", "A1", "A1"],
            "lat": [47.0, 47.01, 47.0],
            "lon": [7.0, 7.01, 7.0],
            "altitude_m": [1000, 1005, 1000],
        }
    )

    station_links = compute_station_aircraft_links(df)
    coverage_links = build_coverage_graph(df, grid_size_deg=0.1)

    assert set(station_links.columns) >= {"station_id", "aircraft_id", "observations"}
    assert len(station_links) == 2
    assert set(coverage_links.columns) >= {"station_id", "grid_id", "observations"}
    assert len(coverage_links) >= 2


def test_rf_graph_builder_and_metrics():
    df = pd.DataFrame(
        {
            "station_id": ["S1", "S2", "S1"],
            "aircraft_id": ["A1", "A1", "A2"],
            "lat": [47.0, 47.0, 47.2],
            "lon": [7.0, 7.0, 7.2],
            "altitude_m": [1000, 1000, 1200],
        }
    )

    graph = build_rf_graph(df, grid_size_deg=0.1)
    metrics = compute_graph_metrics(graph)

    assert "nodes" in graph
    assert "edges" in graph
    assert "metrics" in graph
    assert metrics["connectivity"]["station_count"] == 2
    assert metrics["redundancy"]["aircraft_redundancy_mean"] >= 1.0
    assert "S1" in metrics["station_importance"]
