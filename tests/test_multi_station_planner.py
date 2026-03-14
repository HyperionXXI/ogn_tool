from __future__ import annotations

import pytest

from ogn_tool.analysis.intelligence.multi_station_planner import select_stations_greedy



def test_select_stations_greedy_maximizes_marginal_gain() -> None:
    station_aircraft = {
        "A": {"a1", "a2", "a3"},
        "B": {"a2", "a3", "a4"},
        "C": {"a5", "a6"},
    }

    selected, covered = select_stations_greedy(station_aircraft, k=2)

    assert selected == ["A", "C"]
    assert covered == {"a1", "a2", "a3", "a5", "a6"}



def test_select_stations_greedy_handles_empty_input() -> None:
    selected, covered = select_stations_greedy({}, k=1)

    assert selected == []
    assert covered == set()



def test_select_stations_greedy_is_deterministic_on_ties() -> None:
    station_aircraft = {
        "B": {"a1", "a2"},
        "A": {"a1", "a2"},
    }

    selected, covered = select_stations_greedy(station_aircraft, k=1)

    assert selected == ["A"]
    assert covered == {"a1", "a2"}



def test_select_stations_greedy_validates_k() -> None:
    with pytest.raises(ValueError):
        select_stations_greedy({"A": {"a1"}}, k=0)
