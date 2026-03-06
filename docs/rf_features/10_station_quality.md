Reconstruction du radio horizon 3D

Objectif
Estimer la zone de visibilité radio théorique de la station
et la comparer avec les réceptions observées.

Principe
La portée radio maximale dépend de la hauteur de la station
et de l'altitude de l'émetteur (aircraft).

Le "radio horizon" peut être estimé avec une formule simple
basée sur les altitudes.

Implémentation

1. Définir les paramètres station :

   station_lat
   station_lon
   station_alt_m

2. Charger les paquets avec altitude aircraft valide.

3. Pour chaque paquet calculer :

   distance_km
   aircraft_alt_m

4. Calculer horizon radio théorique :

   horizon_km =
      3.57 * (sqrt(station_alt_m) + sqrt(aircraft_alt_m))

5. Calculer ratio :

   reception_ratio =
      distance_km / horizon_km

6. Construire DataFrame :

   distance_km
   horizon_km
   reception_ratio
   aircraft_alt_m
   azimuth_deg

7. Calculer statistiques globales :

   horizon_mean
   horizon_p95
   observed_p95_distance

8. Calculer efficacité station :

   efficiency =
      observed_p95_distance / horizon_p95