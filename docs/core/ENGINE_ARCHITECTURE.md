# Engine Architecture

Source of truth: docs/core/SYSTEM_ARCHITECTURE.md


Ce document décrit l’architecture des analytics engines du projet ogn_tool. Il précise la structure, les responsabilités, les API, les règles de dépendance, l’orchestration et le mapping code-architecture des moteurs analytiques principaux : RF analysis engine, network intelligence engine, reporting engine.

---

## 1. Analytical Engine Pipeline Diagram

```text
RF packets / observations
	↓
RFAnalysisDataset builder
	↓
RF Analysis Engine
	↓
RFAnalysisResults
	↓
Network Intelligence Engine
	↓
NetworkGraph, network_metrics
	↓
Reporting Engine
	↓
report.json, reporting views
	↓
UI / dashboards / exports
```

---

## 2. Engine API Contracts

### RFAnalysisEngine
- Entrée : RFAnalysisDataset
- Sortie : RFAnalysisResults
- API :
  - run(dataset: RFAnalysisDataset) → RFAnalysisResults

### NetworkIntelligenceEngine
- Entrée : RFAnalysisResults
- Sortie : NetworkGraph, network_metrics
- API :
  - run(results: RFAnalysisResults) → NetworkGraph, network_metrics

### ReportingEngine
- Entrée : NetworkGraph, network_metrics, RFAnalysisResults
- Sortie : report.json, reporting views
- API :
  - build_report(results, network_graph, metrics) → report.json

---

## 3. Dependency and Composition Rules

- Les engines orchestrent, adaptent, publient : aucune logique métier dans les engines.
- RFAnalysisEngine ne dépend que de analysis/normalization, analysis/rf_metrics, analysis/rf_models.
- NetworkIntelligenceEngine ne dépend que de analysis/network_metrics, analysis/network_graph, analysis/intelligence.
- ReportingEngine ne dépend que de reporting/ et des outputs des engines précédents.
- Aucun engine ne doit importer UI, ingestion, ou modifier les datasets en place.
- Toute logique analytique doit résider dans analysis/.

---

## 4. Mapping Code → Architecture

| Engine                    | Modules/Fichiers principaux                                 |
|---------------------------|-------------------------------------------------------------|
| RFAnalysisEngine          | src/ogn_tool/analysis/normalization/, rf_metrics/, rf_models/ |
| NetworkIntelligenceEngine | src/ogn_tool/analysis/network_metrics/, network_graph/, intelligence/ |
| ReportingEngine           | src/ogn_tool/reporting/, report_builder.py, reporting views  |

---

## 5. Engine Orchestration Model

L’exécution du pipeline analytique est orchestrée par le runtime d’analyse.

Exemple de flow :

```python
dataset = build_dataset(observations)

rf_results = RFAnalysisEngine.run(dataset)

network_graph, metrics = NetworkIntelligenceEngine.run(rf_results)

report = ReportingEngine.build_report(
	 rf_results,
	 network_graph,
	 metrics
)
```

---

## 6. Engine Data Immutability Rule

- Les datasets et résultats sont immuables.
- RFAnalysisDataset : jamais modifié in-place
- RFAnalysisResults : outputs analytiques append-only
- NetworkGraph : structure dérivée, jamais modifiée directement

---

## 7. Liens croisés

- [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)
- [RF_ARCHITECTURE.md](RF_ARCHITECTURE.md)
- [ARCHITECTURE_GUARDRAILS.md](ARCHITECTURE_GUARDRAILS.md)
- [DATA_CONTRACT.md](DATA_CONTRACT.md)

---
