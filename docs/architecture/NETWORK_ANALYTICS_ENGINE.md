# Network Analytics Engine Architecture
See also:
   - [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)
   - [INDEX.md](INDEX.md)
Status: Canonical Architecture Specification

> **Reference:** See SYSTEM_ARCHITECTURE.md for the global architecture context.

## Position in the Global Architecture

   ↓
Analytics Engines (network_intelligence, spatial_intelligence, temporal_intelligence)
   ↓
report.json (canonical artifact)
   ↓
Reporting (src/ogn_tool/reporting/)
   ↓
UI / dashboards (apps/)
```

---

## Overview
This document defines the architecture, responsibilities, and contracts of the analytics engine for ogn_tool. It describes the three main analytical layers, their submodules, and the flow from raw report artifacts to actionable network intelligence.

---


## Data Flow and Dependencies

- Each analytics engine (network_intelligence, spatial_intelligence, temporal_intelligence) dépend uniquement de analysis/ (primitives analytiques).
- reporting/ dépend uniquement des analytics engines (jamais l’inverse).
- Les modules ne doivent jamais dépendre d’une couche supérieure.

---

---


## Canonical report.json Contract

Minimal structure:

```
{
   "metadata": {...},
   "rf_metrics": {...},
   "coverage_metrics": {...},
   "network_metrics": {...},
   "diagnostics": {...},
   "recommended_actions": [...]
}
```

---



## Analytics Engines Diagram

```
            report.json
                │
   ┌────────────┬─────────────┬──────────────┬───────────────┐
   │            │             │              │
Network      Spatial        Temporal       Scenario
Intelligence Intelligence  Intelligence   Intelligence
   │            │             │              │
Diagnostics  Coverage      Stability     Network
Risk flags   gaps          activity      planning
Actions      placement     availability  optimization
                                         scenario ranking
---

> **Note:**
> The actual logic for the analytics engines (network, spatial, temporal, scenario) currently resides in `analysis/` and `src/ogn_tool/`.
> The `*_intelligence` directories are not used for real logic at this time and may be empty or removed. Refer to `analysis/` for the canonical implementations.
```

---


## Analytical Layers and Modules


### 1. Network Intelligence Layer
**Responsibility:** Diagnostic réseau à partir des métriques, production d’insights et d’actions.

**Sous-modules :**
- network_diagnostics (SPOF detection, station dominance, redundancy, network confidence)
- network_risk_analysis
- network_recommendations (actions recommandées)
- network_topology_analysis

**Contrat :**
- Input : report.json (network_metrics, diagnostics)
- Output : diagnostics, risk flags, recommended actions


### 2. Spatial Intelligence Engine
**Responsibility:** Analyse géographique du réseau, visualisation et suggestions spatiales.

**Sous-modules :**
- sector_analysis (directional traffic, RF corridors)
- coverage_gap_detection (coverage gaps)
- station_placement_optimizer (station placement)
- geo_export (geojson, map overlays)

**Contrat :**
- Input : report.json (spatial_observations, station_suggestions)
- Output : spatial analytics, geojson layers, map overlays


### 3. Temporal Intelligence Engine

### 4. Scenario Intelligence Engine
**Responsibility:** Network planning, scenario simulation, optimization, station addition/removal, scenario ranking.

**Sous-modules :**
- station_addition_simulation
- station_removal_simulation
- multi_station_planner
- scenario_ranking
- network_priority_scoring
- redundancy_planner

**Contrat :**
- Input : report.json, scenario definitions, network state
- Output : scenario evaluations, planning recommendations, optimization results
**Responsibility:** Analyse temporelle du réseau, stabilité, activité, gaps.

**Sous-modules :**
- availability_analysis (availability)
- activity_model (packet activity)
- temporal_gap_detection (temporal gaps)
- network_stability (stability)

**Contrat :**
- Input : multiple report.json (runs, time series)
- Output : temporal analytics, stability metrics, evolution insights

---


---

- analysis/ = primitives analytiques (calculs, métriques, transformations)
- analytics engines = orchestration, diagnostics, intelligence, outputs
- Ne jamais mélanger les responsabilités.
- Chaque module expose une API stable et des outputs documentés.

---

## Dependency Rule

Allowed dependencies:

- analysis → (no internal dependency to analytics engines)
- network_intelligence → analysis
- spatial_intelligence → analysis
- temporal_intelligence → analysis
- reporting → analytics engines
- apps / UI → reporting

Forbidden dependencies:

- analysis → reporting
- analysis → apps
- analytics engines → UI
- reporting → analysis primitives directly

---


## Canonical Analytics Engine APIs

### Network Intelligence
- analyze_network_health(report)
- detect_spof(report)
- compute_network_redundancy(report)
- generate_recommended_actions(report)

### Spatial Intelligence
- detect_coverage_gaps(report)
- build_rf_corridors(report)
- suggest_station_placements(report)


### Temporal Intelligence
- compute_station_availability(runs)
- detect_temporal_gaps(runs)
- analyze_network_stability(runs)

### Scenario Intelligence
- simulate_station_addition(report, scenario)
- simulate_station_removal(report, scenario)
- plan_multi_station_optimization(report, scenario)
- rank_scenarios(report, scenarios)
- compute_network_priority(report, scenario)
- analysis/ = primitives analytiques (calculs, métriques, transformations)
- analytics engines = orchestration, diagnostics, intelligence, outputs
- Ne jamais mélanger les responsabilités.
- Chaque module expose une API stable et des outputs documentés.

---


---

## Roadmap and Migration
- Étape 1 : Créer les dossiers analytics engines et y ajouter des wrappers qui appellent analysis/.
- Étape 2 : Stabiliser les API, migrer progressivement la logique.
- analysis/ reste le socle de primitives jusqu’à migration complète.
- Ce document est la référence unique pour l’architecture analytics.

---

## Anti-patterns to Avoid
- Do not multiply documentation files for each submodule.
- Avoid mixing responsibilities between modules.
- Ensure all analytics outputs are documented here.

---

## Revision History
- 2026-03-16: Initial structure and contracts drafted.
