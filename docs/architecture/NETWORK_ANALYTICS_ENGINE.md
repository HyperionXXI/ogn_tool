
# Network Analytics Engine Architecture

## Position in the Global Architecture

```
APRS / OGN data
   ↓
Data repositories
   ↓
RF Engine
   ↓
Analysis primitives (src/ogn_tool/analysis/)
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

## Module Boundaries and Migration Rule
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
