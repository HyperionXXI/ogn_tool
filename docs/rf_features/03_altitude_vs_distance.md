Analyse altitude vs distance (propagation radio)
Objectif
Analyser la portée radio en fonction de l'altitude de l'aéronef.

Principe
La portée radio dépend fortement de l'altitude de l'émetteur.

Implémentation
1. Extraire altitude depuis les trames OGN.
2. Calculer distance station → aircraft.
3. Construire DataFrame:
   altitude_m
   distance_km

4. Regrouper altitude en bins:
   0–500 m
   500–1000 m
   1000–2000 m
   >2000 m

5. Calculer pour chaque bin:
   - distance moyenne
   - distance P95
   - distance max

Visualisation
Scatter plot altitude vs distance
+ boxplot par bin d'altitude.

Interface
Ajouter section:
"Altitude vs RX distance".

Optimisation
- limiter les données aux 30 derniers jours