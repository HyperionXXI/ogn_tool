from __future__ import annotations

from ogn_tool.intelligence.multi_station_planner import (
    select_stations_greedy,
    select_stations_lazy_greedy,
)



def test_weighted_none_matches_original_greedy() -> None:
    station_aircraft = {
        "A": {"a", "b"},
        "B": {"b", "c"},
    }

    s1, c1 = select_stations_greedy(station_aircraft, 1)
    s2, c2 = select_stations_greedy(station_aircraft, 1, aircraft_weights=None)

    assert s1 == s2
    assert c1 == c2



def test_weighted_planner_prefers_rare_aircraft_greedy() -> None:
    station_aircraft = {
        "A": {"rare"},
        "B": {"dense"},
    }
    weights = {
        "rare": 10.0,
        "dense": 1.0,
    }

    selected, covered = select_stations_greedy(
        station_aircraft,
        1,
        aircraft_weights=weights,
    )

    assert selected == ["A"]
    assert covered == {"rare"}



def test_weighted_planner_prefers_rare_aircraft_lazy() -> None:
    station_aircraft = {
        "A": {"rare"},
        "B": {"dense"},
    }
    weights = {
        "rare": 10.0,
        "dense": 1.0,
    }

    selected, covered = select_stations_lazy_greedy(
        station_aircraft,
        1,
        aircraft_weights=weights,
    )

    assert selected == ["A"]
    assert covered == {"rare"}



def test_weighted_lazy_matches_weighted_greedy() -> None:
    station_aircraft = {
        "A": {"a", "b"},
        "B": {"b", "c"},
        "C": {"d"},
    }
    weights = {
        "a": 1.0,
        "b": 1.0,
        "c": 3.0,
        "d": 2.0,
    }

    greedy_selected, greedy_covered = select_stations_greedy(
        station_aircraft,
        2,
        aircraft_weights=weights,
    )
    lazy_selected, lazy_covered = select_stations_lazy_greedy(
        station_aircraft,
        2,
        aircraft_weights=weights,
    )

    assert greedy_selected == lazy_selected
    assert greedy_covered == lazy_covered
