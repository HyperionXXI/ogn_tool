from __future__ import annotations

import heapq


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



def select_stations_lazy_greedy(
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

    covered: set[str] = set()
    selected: list[str] = []
    heap: list[tuple[int, str]] = []

    for station_id in sorted(remaining):
        gain = len(remaining[station_id])
        heapq.heappush(heap, (-gain, station_id))

    while heap and len(selected) < k:
        while True:
            neg_gain, station_id = heapq.heappop(heap)
            aircraft = remaining[station_id]
            real_gain = len(aircraft - covered)

            if not heap:
                break

            next_estimated_gain = -heap[0][0]
            if real_gain >= next_estimated_gain:
                break

            heapq.heappush(heap, (-real_gain, station_id))

        selected.append(station_id)
        covered |= remaining[station_id]
        del remaining[station_id]

    return selected, covered


__all__ = ["select_stations_greedy", "select_stations_lazy_greedy"]
