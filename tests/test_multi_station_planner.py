from __future__ import annotations

import pytest

from ogn_tool.intelligence.multi_station_planner import (
    select_stations_greedy,
    select_stations_lazy_greedy,
)



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



def test_select_stations_lazy_greedy_handles_empty_input() -> None:
    result = select_stations_lazy_greedy({}, 2)

    assert result == ([], set())



def test_select_stations_lazy_greedy_validates_k() -> None:
    with pytest.raises(ValueError):
        select_stations_lazy_greedy({"A": {"x"}}, 0)



def test_select_stations_lazy_greedy_matches_greedy() -> None:
    station_aircraft = {
        "A": {"a", "b"},
        "B": {"b", "c"},
        "C": {"d"},
    }

    greedy, cov1 = select_stations_greedy(station_aircraft, 2)
    lazy, cov2 = select_stations_lazy_greedy(station_aircraft, 2)

    assert greedy == lazy
    assert cov1 == cov2



def test_select_stations_lazy_greedy_is_deterministic() -> None:
    station_aircraft = {
        "A": {"a", "b"},
        "B": {"b", "c"},
        "C": {"c", "d"},
    }

    r1 = select_stations_lazy_greedy(station_aircraft, 2)
    r2 = select_stations_lazy_greedy(station_aircraft, 2)

    assert r1 == r2



def test_select_stations_lazy_greedy_tie_breaks_lexicographically() -> None:
    station_aircraft = {
        "A": {"a"},
        "B": {"b"},
        "C": {"c"},
    }

    selected, covered = select_stations_lazy_greedy(station_aircraft, 2)

    assert selected == ["A", "B"]
    assert covered == {"a", "b"}
