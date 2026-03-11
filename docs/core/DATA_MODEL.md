STATUS: canonical
SOURCE_OF_TRUTH: docs/DATA_MODEL.md

This document is subordinate to docs/core/ROADMAP_MASTER.md. If contradictions exist, ROADMAP_MASTER.md is the canonical source.

# Data Model

## packets

Raw packets received from APRS.

Fields:

timestamp  
aircraft_id  
lat  
lon  
altitude  
station_id  
rssi  

---

## radio_events

A single aircraft emission that may be received by multiple stations.

event_id  
timestamp  
aircraft_id  
lat  
lon  
altitude  
stations_receiving  

---

## coverage_grid

Spatial grid used for coverage analysis.

cell_id  
lat  
lon  
packet_density  
aircraft_count  
station_count  
confidence  

---

## station_metrics

Computed metrics for each station.

station_id  
packet_count  
aircraft_count  
max_distance  
p95_distance  
coverage_cells  
contribution_score  

---

## network_metrics

Global network metrics.

coverage_ratio  
redundancy_ratio  
blind_zone_ratio  
network_resilience_score  

