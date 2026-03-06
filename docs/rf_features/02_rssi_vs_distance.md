Courbe signal RSSI vs distance
Objectif
Diagnostiquer la performance radio de la station.

Principe
Tracer RSSI (ou signal dB) en fonction de la distance.

Implémentation
1. Extraire depuis les trames :
   - signal strength
   - distance calculée
2. Filtrer :
   - distance < 100 km
   - signal valide
3. Construire un DataFrame:
   columns: distance_km, rssi_db

4. Calculer:
   - moyenne RSSI par bin de distance (ex: 1 km)

Visualisation
Scatter plot:
x = distance_km
y = rssi_db

+ courbe moyenne.

Interface
Ajouter un panneau:
"Signal vs distance".

Optimisation
- downsampling scatter (max 10k points)