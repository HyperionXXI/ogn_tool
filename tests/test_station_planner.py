import pandas as pd

from ogn_tool.analysis.intelligence.station_planner import detect_blind_zones, suggest_station_locations


def test_station_planner_detects_blind_zones():
    coverage = pd.DataFrame({
        "grid_lat": [47.0, 47.1],
        "grid_lon": [7.0, 7.1],
        "stations": [1, 3],
    })
    blind = detect_blind_zones(coverage)
    assert len(blind) == 1


def test_station_planner_suggests_locations():
    coverage = pd.DataFrame({
        "grid_lat": [47.0, 47.1],
        "grid_lon": [7.0, 7.1],
        "stations": [1, 1],
    })
    graph = {"metrics": {"blind_zones": {"count": 2}}}
    suggestions = suggest_station_locations(graph, coverage)
    assert len(suggestions) == 2
