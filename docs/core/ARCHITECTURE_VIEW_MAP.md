# Architecture View Map

Ce document cartographie les vues d’architecture du projet ogn_tool, leur rôle, leur responsabilité principale et leurs liens croisés. Il sert de référence pour maintenir la cohérence documentaire et éviter la dérive des responsabilités.

---

| Vue / Document                | Rôle principal                        | Propriétaire des sujets                | Liens croisés principaux                |
|------------------------------|---------------------------------------|----------------------------------------|-----------------------------------------|
| SYSTEM_ARCHITECTURE.md       | Modèle système global                 | Structure, composants, data flow       | RF_ARCHITECTURE, ENGINE_ARCHITECTURE, ARCHITECTURE_GUARDRAILS |
| RF_ARCHITECTURE.md           | Vue métier RF                         | Pipeline RF, métriques, niveaux d’analyse | SYSTEM_ARCHITECTURE, ENGINE_ARCHITECTURE |
| ENGINE_ARCHITECTURE.md       | Architecture des analytics engines    | RF engine, network engine, reporting engine | SYSTEM_ARCHITECTURE, RF_ARCHITECTURE    |
| ARCHITECTURE_GUARDRAILS.md   | Invariants et contraintes             | Règles, interdictions, domain model    | SYSTEM_ARCHITECTURE, DATA_CONTRACT      |
| DATA_CONTRACT.md             | Contrats de données typés             | Interfaces, schémas, artefacts         | ARCHITECTURE_GUARDRAILS, ENGINE_ARCHITECTURE |
| ARCHITECTURE_OVERVIEW.md     | Navigation documentaire               | Orientation, liens, structure globale  | Toutes les vues principales             |

---

## Règles de responsabilité
- Chaque vue est propriétaire de son sujet : elle doit être la référence unique pour ce domaine.
- Les redondances sont acceptables pour la lisibilité, mais la responsabilité doit rester claire.
- Toute nouvelle vue doit être ajoutée à cette map et référencée dans ARCHITECTURE_OVERVIEW.md.

## Prochaine étape
- Nettoyer les documents existants pour aligner leur contenu avec cette map.
- Créer ENGINE_ARCHITECTURE.md si elle n’existe pas encore.
