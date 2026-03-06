Objectif
Détecter automatiquement si la station présente un problème
d’antenne ou de positionnement (mauvaise orientation, obstacles, installation).

Principe
Analyser la distribution des distances et du signal par direction.
Une station correcte doit avoir une couverture relativement homogène.
Une asymétrie forte ou une chute rapide du RSSI indique un problème.

Implémentation

1. Calculer pour chaque paquet :

   distance_km
   azimuth_deg
   rssi_db (si disponible)

2. Diviser l’espace en secteurs angulaires (ex : 12 secteurs de 30°).

3. Pour chaque secteur calculer :

   count_packets
   mean_distance
   p95_distance
   mean_rssi

4. Construire un DataFrame :

   sector_deg
   packet_count
   mean_distance
   p95_distance
   mean_rssi

5. Calculer des indicateurs d’asymétrie :

   distance_ratio =
       max(p95_distance) / min(p95_distance)

   traffic_ratio =
       max(packet_count) / min(packet_count)

6. Détection automatique :

   si distance_ratio > 3
      → possible obstacle / relief

   si traffic_ratio > 4
      → couverture très asymétrique

   si mean_rssi très faible < 10 km
      → problème antenne probable

Visualisation

Créer un graphique radar (polar chart) :

   angle = secteur
   rayon = p95_distance

Ajouter un tableau diagnostic :

   direction
   p95_distance
   mean_rssi
   packet_count

Interface

Ajouter une section :

   "Station health diagnostics"

Afficher :

   ✓ couverture équilibrée
   ⚠ asymétrie de réception
   ⚠ RSSI faible