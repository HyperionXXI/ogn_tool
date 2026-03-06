Détection automatique d’un mauvais emplacement de station

Objectif
Détecter automatiquement si la station est mal positionnée
(antenne derrière une fenêtre, trop basse, obstacle proche).

Principe
Une station mal placée présente plusieurs symptômes :

- très peu de paquets proches
- RSSI faible même à courte distance
- distance maximale faible
- couverture très directionnelle

Implémentation

1. Calculer pour chaque paquet :

   distance_km
   azimuth_deg
   rssi_db (si disponible)

2. Définir trois zones autour de la station :

   zone_near      : 0–3 km
   zone_mid       : 3–10 km
   zone_far       : 10–30 km

3. Calculer pour chaque zone :

   packet_count
   mean_rssi
   mean_distance

4. Calculer des indicateurs :

   near_density =
      packets_near / packets_total

   near_rssi_mean

   far_reception_ratio =
      packets_far / packets_total

5. Détection heuristique

   cas 1 : near_density très faible
           → station probablement en intérieur

   cas 2 : near_rssi_mean faible
           → antenne mauvaise ou atténuation

   cas 3 : far_reception_ratio très faible
           → station trop basse

6. Score de qualité station

   station_quality_score =
      weighted_sum(
        near_density,
        far_reception_ratio,
        mean_rssi
      )

7. Classer :

   score > 0.7
   → station bien placée

   0.4–0.7
   → station correcte

   <0.4
   → station mal placée