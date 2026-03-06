Carte polaire de réception (direction vs distance)
Objectif
Ajouter une analyse de couverture radio directionnelle pour la station.

Principe
Calculer la distance moyenne de réception par direction (0–360°).

Implémentation
1. Pour chaque paquet avec lat/lon valide :
   - calculer distance et azimut par rapport à la station.
2. Regrouper les paquets par secteur angulaire (ex: 10° ou 15°).
3. Calculer pour chaque secteur :
   - distance moyenne
   - distance max
   - nombre de paquets
4. Stocker le résultat dans un DataFrame.

Visualisation
Créer un graphique polaire (Plotly ou matplotlib polar):
- angle = direction
- rayon = distance moyenne

Interface
Ajouter une section dans le dashboard:
"Radio coverage polar diagram".

Contraintes
- utiliser numpy vectorisé
- limiter les points (échantillonnage possible)