from ogn_tool.runtime.scenario_api import (
    analyze_station_addition,
    analyze_station_removal,
    rank_station_addition_candidates,
)


def test_scenario_api_exports_runtime_entrypoints() -> None:
    assert callable(analyze_station_addition)
    assert callable(analyze_station_removal)
    assert callable(rank_station_addition_candidates)
