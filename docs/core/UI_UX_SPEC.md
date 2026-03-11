STATUS: canonical
SOURCE_OF_TRUTH: docs/UI_UX_SPEC.md

This document is subordinate to docs/ROADMAP_MASTER.md.
If contradictions exist, ROADMAP_MASTER.md is the canonical source.

# UI / UX Specification

This document defines the user interface for the RF Network Observatory.

The system is not a traditional dashboard but a network observatory
allowing exploration, inspection and analysis of RF reception data.

The interface is map-centric and object-driven.

---

# UI Philosophy

The UI follows four principles:

map-first exploration  
object-centric inspection  
layer-based visualization  
analysis overlays  

The interface should resemble modern network observatories or telemetry
interfaces such as satellite network monitoring systems.

---

# Dashboard Architecture

The dashboard uses a three-panel layout.

LEFT PANEL

navigation and filters.

CENTER PANEL

interactive map.

RIGHT PANEL

object inspector.

Layout concept:

Navigation | Map | Inspector

The map is always the central element.

---

# Views

The interface exposes the following main views.

RF Network

Global view of the RF reception network.
Displays stations, aircraft and reception density.

Network Intelligence

Analytical view of the network structure.
Displays redundancy, blind zones and weak reception areas.

RF Observatory

Real-time monitoring view.
Shows live aircraft, packet reception and station activity.

Aircraft Layer

Aircraft-centered analysis.
Shows aircraft trajectories and multi-station reception patterns.

Station Lab

Station analysis environment.
Used to inspect station coverage and RF footprint.

---

# Map Layers

The map supports multiple overlay layers.

Stations  
Aircraft  
Reception points  
Coverage grid  
Blind zones  
Network redundancy  
Propagation estimation  
Station influence zones  

Layers can be toggled individually.

---

# Object Inspector

The right panel displays contextual information when an object is selected.

Selectable objects:

station  
aircraft  
grid cell  
coverage region  

Inspector information may include:

metadata  
packet statistics  
reception density  
visibility estimation  
network redundancy information  

---

# Interaction Model

Primary interactions include:

map pan  
map zoom  
layer toggling  
object selection  
time window filtering  

Selecting an object opens the inspector panel.

---

# RF Model Integration

The UI can expose analysis outputs from RF models.

Examples include:

rf_visibility_model  
rf_blind_zone_detection  
station_placement_optimizer  
coverage_estimation  

These models may provide overlays or inspector data.

---

# Expected Behaviour

The UI must prioritize exploration and network understanding.

The interface should allow users to:

observe the RF network  
detect blind zones  
analyze reception quality  
inspect stations  
explore aircraft reception patterns  

The map must always remain the primary visualization surface.
