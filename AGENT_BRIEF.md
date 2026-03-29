# OGN Tool — AGENT BRIEF (Network Intelligence Engine)

## 1) Objectif produit

Construire un **OGN Network Intelligence Engine** (et non un FlightRadar).

Le système doit permettre de répondre rapidement (≤ 3 secondes) à :

- Où le réseau capte réellement
- Où il est aveugle
- Ce qu’une station apporte (unique vs redondant)
- Quelles actions réseau sont pertinentes

---

## 2) Contraintes d’architecture (NON NÉGOCIABLES)

Architecture stricte :

- Kernel: calcul pur
- Domain: sémantique métier
- Intelligence: inférence / décision
- Reporting: contrat canonique + vues
- UI: projection uniquement (aucune logique métier)

Interdits :

- fallback legacy
- multi-path implicites
- wrappers analysis
- logique métier côté frontend

---

## 3) Contrat de données actuel (résumé)

Payload `/api/payload` contient typiquement :

- `network_summary`
- `stations`
- `metrics`
  - stations
  - links
  - coverage
  - blind_zones
  - risk_zones
- `intelligence.rf_analysis`
  - rf_signature
  - rf_directional_gaps
  - rf_gap_structure
  - rf_shadow_analysis

Problème actuel :

Les runs ne fournissent pas toujours des positions aircraft exploitables.

---

## 3bis) Unité canonique d’observation réseau (CRITIQUE)

Le moteur réseau ne doit **JAMAIS** raisonner directement sur des packets.

Unité canonique obligatoire :

```python
aircraft_observation = {
  "aircraft_id": "str",
  "lat": "float",
  "lon": "float",
  "timestamp": "datetime",
  "seen_by": ["station_id", "..."]
}
```

### Règles

- `seen_by` provient d’une **corrélation multi-stations réelle**
- aucune inférence heuristique de `seen_by`
- aucun fallback mono-station pour qualifier “network”
- une observation mono-station ≠ preuve réseau

### Projection UI

```python
metrics.aircraft_positions = projection(aircraft_observations)
```

- ce champ est une **projection simplifiée**
- ce n’est jamais une source primaire

---

## 4) État frontend actuel

Fichiers :

- `frontend/app.js`
- `frontend/rf_layers.js`
- `frontend/aircraft_layers.js`
- `frontend/index.html`

### Fonctionnel

- rendu deck.gl
- cône RF
- gaps / direction
- overlays

### Limites

- aircraft_positions souvent vide
- rendu abstrait (“pizza RF”)
- UI non décisionnelle

---

## 5) Backend API

Fichier :

- `apps/api_server.py`

Fonction :

- sert frontend statique
- expose `/api/payload?run_id=...`
- enrichit coords station
- tente d’ajouter aircraft_positions depuis DB

### Attention

- DB path dépend de `run_metadata.json`
- DB absente → pas d’aircraft_positions

---

## 6) Problèmes connus (ne pas re-diagnostiquer)

- CORS (localhost vs 127.0.0.1)
- warnings WebGL Firefox (non bloquants)
- UI vide ≠ bug → souvent payload pauvre

---

## 7) Éléments validés

- pipeline run → report → payload OK
- RF signature / gaps / structure OK
- scripts qualité existants
- moteur RF stable

---

## 8) Priorités

### P0 (OBLIGATOIRE)

Construire la source de vérité réseau :

```text
aircraft_observations
```

Puis exposer :

```text
metrics.aircraft_positions
```

Sans cette couche :

→ aucune intelligence réseau possible

---

### P1

Construire :

```text
spatial_network_features
```

Dans reporting backend :

- coverage_density
- unique_coverage
- shared_coverage
- blind_zones
- grid_meta

---

### P2

UI orientée décision :

- heatmap unique (primaire)
- heatmap shared (secondaire)
- blind overlay
- RF en contexte uniquement

---

## 9) Règles UI (STRICTES)

La UI ne calcule jamais :

- unique
- shared
- blind

La UI affiche uniquement :

```text
spatial_network_features
```

---

## 10) Validité d’un run

Un run "Network Intelligence" est valide uniquement si :

```text
aircraft_observations non vide
```

Sinon :

Mode :

```text
RF-only diagnostic
```

Message UI obligatoire :

```text
network inference unavailable
```

---

## 11) Commandes utiles

```bash
uvicorn apps.api_server:app --reload
```

Puis :

- http://localhost:8000
- http://localhost:8000/api/payload?run_id=<RUN_ID>

Debug navigateur :

```js
const r = await fetch('/api/payload?run_id=<RUN_ID>');
const p = await r.json();
console.log(p.metrics?.aircraft_positions?.length);
```

## 12) Règles d’exécution pour l’IA

- ne pas toucher au frontend tant que P0 n’est pas résolu
- ne pas ajouter de métriques
- ne pas casser le contrat existant
- ajouter uniquement des champs additifs
- toujours valider sur un run réel (pas mock)

## 13) Ligne directrice

Toujours raisonner :

```text
network → spatial → décision
```

Jamais :

```text
RF → visualisation → interprétation
```

## 14) Définition de succès

L’utilisateur doit pouvoir répondre en moins de 3 secondes :

- où la station apporte de la valeur
- où elle est redondante
- où le réseau est aveugle
- quelle action prioriser

---

## Retour final

Le projet est structurellement sain :

- modèle canonique clair
- verrou conceptuel fort (3bis)
- séparation des couches respectée
- roadmap réaliste

Risque principal restant : **la qualité réelle des `aircraft_observations`**.

Bascule projet :

```text
proto RF → système d’ingénierie réseau
```
