Comparaison station vs iGates voisines

Objectif
Comparer la performance radio de la station locale
avec les autres iGates OGN dans la même région.

Principe
Si plusieurs stations reçoivent les mêmes aircraft,
on peut comparer :

- nombre de paquets reçus
- distance moyenne
- distance P95

Implémentation

1. Charger les paquets dans la fenêtre temporelle choisie.

2. Identifier les igates présents :

   SELECT igate, count(*) FROM packets GROUP BY igate

3. Garder les igates avec suffisamment de trafic :

   min_packets > 1000

4. Pour chaque igate calculer :

   total_packets
   mean_distance
   p95_distance
   max_distance

5. Construire DataFrame :

   igate
   packet_count
   mean_distance
   p95_distance
   max_distance

6. Identifier la station locale :

   station_callsign

7. Calculer :

   performance_score =
       p95_distance_station /
       median(p95_distance_all)

Visualisation

Ajouter une section dashboard :

"Station performance vs network"

Graphiques :

1. bar chart
   p95_distance par igate

2. ranking table
   classement des stations

Interface

Afficher :

Station rank
Performance score
Comparaison moyenne réseau

Exemple :

Station FK50887
rank: 3 / 12
performance score: 1.18