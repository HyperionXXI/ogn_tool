from __future__ import annotations


def select_stations_greedy(
    station_aircraft: dict[str, set[str]],
    k: int,
) -> tuple[list[str], set[str]]:
    if k < 1:
        raise ValueError("k must be >= 1")

    remaining = {
        station_id: set(aircraft)
        for station_id, aircraft in station_aircraft.items()
        if aircraft
    }
    if not remaining:
        return [], set()

    selected: list[str] = []
    covered: set[str] = set()

    while len(selected) < k and remaining:
        best_station = None
        best_gain = -1

        for station_id in sorted(remaining):
            aircraft = remaining[station_id]
            gain = len(aircraft - covered)
            if gain > best_gain:
                best_gain = gain
                best_station = station_id

        if best_station is None:
            break

        selected.append(best_station)
        covered |= remaining[best_station]
        del remaining[best_station]

    return selected, covered


__all__ = ["select_stations_greedy"]
