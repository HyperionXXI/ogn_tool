from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MultiStationCoverageEvaluation:
    """
    Deduplicated aircraft coverage evaluation for a set of stations.

    stations:
        sorted list of station identifiers included in the evaluation

    unique_aircraft_supported:
        number of unique aircraft seen by at least one station

    total_station_aircraft:
        sum of aircraft counts across stations (duplicates included)

    overlapping_aircraft:
        number of duplicated aircraft observations across stations

    redundancy_factor:
        ratio unique_aircraft_supported / total_station_aircraft

        Interpretation:
        - 1.0 -> no overlap (perfect efficiency)
        - <1.0 -> stations observe many of the same aircraft
    """

    stations: list[str]
    unique_aircraft_supported: int
    total_station_aircraft: int
    overlapping_aircraft: int
    redundancy_factor: float
