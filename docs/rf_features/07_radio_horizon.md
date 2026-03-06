Couverture radio avec relief (analyse terrain)
Objectif
Améliorer l’analyse de couverture radio en intégrant le relief
afin de comprendre l’impact des montagnes et vallées.

Principe
Comparer la distance de réception observée avec
la ligne de vue théorique basée sur le relief.

Implémentation

1. Charger un modèle numérique de terrain (DEM)
   ex: SRTM / Copernicus / EU DEM.

2. Stocker la position de la station :

   station_lat
   station_lon
   station_alt

3. Pour chaque paquet avec position valide :

   aircraft_lat
   aircraft_lon
   aircraft_alt

4. Calculer :

   distance_km
   azimuth_deg

5. Calculer la ligne de vue théorique :

   radio_horizon_km =
       3.57 * (sqrt(station_alt_m) + sqrt(aircraft_alt_m))

6. Comparer :

   reception_efficiency =
       distance_km / radio_horizon_km

7. Construire DataFrame :

   lat
   lon
   distance_km
   reception_efficiency
   azimuth_deg

Visualisation

Carte 2D :

   points colorés par reception_efficiency

   vert  : bonne réception
   orange: réception partielle
   rouge : réception faible

Option avancée :

   overlay relief (hillshade)

Interface

Ajouter section dashboard :

   "Terrain-aware radio coverage"

Options utilisateur :

   activer / désactiver relief
   filtre altitude aircraft
   rayon analyse (ex 100 km)

Optimisation

- précharger DEM en mémoire
- utiliser rasterio ou xarray
- limiter analyse aux 30 derniers jours


Ce que cette analyse apportera au projet

Avec cette fonction, l'outil pourra montrer :

zones masquées par le relief

portée réelle vs portée théorique

efficacité de la station

Dans une région comme le Jura, cela révélera immédiatement :

les vallées bloquées

les crêtes qui améliorent la portée

l’effet d’une antenne placée trop bas.