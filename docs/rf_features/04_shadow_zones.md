Détection automatique des zones d’ombre radio
Objectif
Identifier automatiquement les zones géographiques où des aircraft sont visibles
par le réseau OGN mais rarement ou jamais reçus par la station locale.

Principe
Comparer les positions aircraft reçues par la station avec les positions
globalement visibles sur le réseau (autres igates).

Une zone où:
- aircraft présents
- mais rarement reçus par la station
= zone d’ombre radio.

Implémentation

1. Charger les paquets dans la fenêtre temporelle sélectionnée.

2. Construire deux ensembles de données :

   A) GLOBAL_TRAFFIC
   - toutes les positions aircraft
   - indépendamment de l’igate

   B) LOCAL_RX
   - positions aircraft reçues par la station analysée
   - filtrées par signature de flux (igate/qas)

3. Diviser la zone géographique en grille régulière
   (ex: cellules de 2 km ou 5 km).

4. Pour chaque cellule :

   compter
   - aircraft_global_count
   - aircraft_local_rx_count

5. Calculer un indicateur :

   reception_ratio = local_rx / global

6. Définir seuils :

   reception_ratio > 0.6
   → couverture normale

   reception_ratio 0.2–0.6
   → couverture partielle

   reception_ratio < 0.2
   → zone d’ombre probable

7. Construire un DataFrame :

   grid_lat
   grid_lon
   aircraft_global
   aircraft_local
   reception_ratio

Visualisation

Créer une heatmap sur la carte :

couleur cellule :

vert
bonne réception

orange
réception partielle

rouge
zone d’ombre radio

Interface

Ajouter un panneau dashboard :

"Radio shadow map"

Options utilisateur :

- taille grille (2 km / 5 km / 10 km)
- fenêtre temporelle
- filtre altitude

Optimisation

- limiter analyse aux 30 derniers jours
- pré-calculer la grille
- utiliser pandas groupby vectorisé