import pandas as pd

from ogn_tool.network.network_intelligence import (
    compute_network_topology,
    compute_station_roles
)


def test_network_topology():

    df = pd.DataFrame({
        "src": ["A1", "A2"],
        "igate": ["S1", "S1"],
        "lat": [47.0, 47.1],
        "lon": [7.0, 7.1],
        "ts_epoch": [1, 2]
    })

    topo = compute_network_topology(df)

    assert "nodes" in topo
    assert "edges" in topo


def test_station_roles():

    df = pd.DataFrame({
        "src": ["A1", "A2", "A3"],
        "igate": ["S1", "S1", "S2"],
        "lat": [47, 47, 47],
        "lon": [7, 7, 7],
        "ts_epoch": [1, 2, 3]
    })

    roles = compute_station_roles(df)

    assert "S1" in roles
