from ogn_tool.analysis.network_metrics import (
    build_network_metrics,
    build_reception_events,
    build_station_metrics,
    build_station_reception,
    compute_blind_zones,
    compute_coverage_redundancy,
    compute_station_overlap,
    detect_network_blind_zones,
    enrich_coverage_grid,
)


# Canonical engine naming
build_radio_events = build_reception_events
compute_network_blind_zones = detect_network_blind_zones


__all__ = [
    "build_network_metrics",
    "build_radio_events",
    "build_station_metrics",
    "build_station_reception",
    "compute_blind_zones",
    "compute_coverage_redundancy",
    "compute_network_blind_zones",
    "compute_station_overlap",
    "enrich_coverage_grid",
]
