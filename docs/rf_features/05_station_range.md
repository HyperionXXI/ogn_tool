Détection automatique de problème d’antenne / station
Estimation automatique de la portée radio maximale
Objectif
Estimer automatiquement la portée radio maximale réelle de la station.

Principe
La portée maximale observée (max distance) est instable et dépend
d'événements rares. Une estimation robuste peut être obtenue via
la distance P95 ou P99 (percentile) des réceptions.

Implémentation

1. Charger les paquets avec position valide (lat/lon).

2. Calculer pour chaque paquet :
   distance_km = distance(station, aircraft)

3. Filtrer les données pour éviter les artefacts :
   - distance_km < 200 km
   - altitude aircraft > 100 m
   - signal valide si disponible

4. Calculer plusieurs indicateurs :

   max_distance
   p99_distance
   p95_distance
   median_distance

5. Calculer également la portée par tranche d'altitude :

   bins altitude :
   0–500 m
   500–1000 m
   1000–2000 m
   >2000 m

   pour chaque bin calculer :
   p95_distance
   max_distance

6. Construire un DataFrame :

   altitude_bin
   p95_distance
   max_distance
   sample_count

Visualisation

Ajouter un panneau dashboard :

"Station radio range estimate"

Afficher :

- métriques globales
- graphique altitude vs distance_p95

Interface

Afficher :

Estimated station range = p95_distance

avec texte explicatif :

"La portée radio correspond à la distance à laquelle 95 % des
réceptions se produisent."

Optimisation

- limiter aux 30 derniers jours
- utiliser pandas vectorisé