🇫🇷 Français | 🇬🇧 [English version](README.md)

# ogn_tool — Intelligence réseau RF pour OGN / FLARM / FANET

`ogn_tool` est un moteur d’analyse RF et d’intelligence réseau pour les
**réseaux de stations sol OGN / FLARM / FANET**.

Le projet a commencé comme un analyseur de couverture RF centré station,
puis a évolué vers un moteur analytique structuré capable de :

- analyser des observations RF réelles
- diagnostiquer les faiblesses d’une station ou d’un réseau
- simuler des scénarios de panne réseau
- prioriser les améliorations de couverture et de redondance
- produire des rapports réseau orientés opérateur

Le dashboard Streamlit actuel est une UI consommatrice. Ce n’est plus le
cœur du produit.

---

## Pourquoi Ce Projet Existe

De nombreux outils savent afficher des positions d’aéronefs.

Beaucoup plus rares sont ceux qui permettent de répondre à des
questions d’ingénierie sur le réseau d’observation RF lui-même.

`ogn_tool` existe pour analyser le comportement réel des réseaux
d’observation RF et transformer les données de réception brutes en
décisions exploitables, par exemple :

- quelle station est faible
- quelle station est critique
- où la couverture est insuffisante
- où il faut ajouter de la redondance
- quel gain une nouvelle station pourrait apporter

Le projet vise donc non seulement la visualisation, mais aussi le
**diagnostic, le raisonnement et la planification** pour les réseaux RF
distribués.

---

## Terminologie

Dans ce dépôt, les termes suivants ont un sens strict :

- `analysis` : calcule des faits RF ou réseau mesurables
- `intelligence` : dérive des diagnostics, priorités et scénarios
  exploitables à partir des sorties analytiques
- `reporting` : assemble des synthèses orientées opérateur à partir des
  résultats runtime typés
- `UI` : affiche, filtre et formate les résultats sans les recalculer
- `results.*` : API runtime typée officielle exposée aux consommateurs

### Glossaire Domaine

- `OGN` : Open Glider Network, réseau distribué qui collecte et partage
  des données de suivi d’aéronefs et de réception radio
- `FLARM` : système d’alerte anticollision et de suivi largement utilisé
  dans le vol à voile et l’aviation légère
- `FANET` : Flying Ad-hoc Network, protocole radio léger orienté maillage
  aérien, utilisé notamment dans les écosystèmes de vol libre
- `APRS` : Automatic Packet Reporting System, réseau d’échange par
  paquets pour positions et télémétrie
- `APRS-IS` : réseau de serveurs APRS reliés à Internet qui relaient le
  trafic APRS
- `RF` : radio frequency, c’est-à-dire la radiofréquence
- `SPOF` : single point of failure, point unique de panne
- `RSSI` : received signal strength indicator, indicateur de puissance
  reçue
- `UI` : user interface, interface utilisateur

---

## Ce Que Fait Le Projet

À haut niveau, `ogn_tool` aide à répondre à des questions comme :

- Quelle est la performance réelle d’une station ?
- Quelles stations sont critiques dans le réseau ?
- Où se trouvent les trous de couverture ?
- Que se passe-t-il si une station disparaît ?
- Où faut-il ajouter de la redondance en priorité ?
- Quel emplacement candidat pourrait améliorer le réseau ?

Le projet est donc utile à la fois pour le **diagnostic RF** et pour
l’**ingénierie réseau**.

---

## Architecture En Une Vue

Le projet est organisé en couches :

```text
ingestion
  -> normalization
  -> analysis
  -> intelligence
  -> reporting
  -> UI
```

Responsabilités :

- `analysis` : calcule des métriques RF et réseau mesurables
- `intelligence` : dérive des diagnostics et scénarios exploitables
- `reporting` : assemble des synthèses orientées opérateur
- `apps/ui` : affiche les résultats

La surface runtime officielle est `results.*`, en particulier
`results.network_metrics`.

---

## Capacités Actuelles

### Diagnostic RF

- analyse polaire de couverture
- analyse RSSI vs distance
- analyse altitude vs distance
- détection de zones d’ombre radio
- estimation de portée station
- diagnostic d’antenne
- analyse de l’horizon radio
- analyse des limitations dues au relief
- comparaison multi-stations

### Intelligence réseau

- diagnostic de santé des stations
- synthèse réseau
- analyse de dépendance entre stations
- détection de point unique de panne (SPOF)
- simulation de perte de station
- planification de redondance
- détection de trous de couverture
- priorisation des trous de couverture
- simulation empirique d’ajout de station

### Reporting

- constructeur typé de rapport d’ingénierie réseau
- couche de reporting fondée sur les résultats runtime typés

---

## Points D’Entrée Du Dépôt

Si vous découvrez le dépôt, commencez ici :

- `README.fr.md`
- `docs/ARCHITECTURE.md`
- `docs/architecture/INDEX.md`
- `docs/architecture/OPERATIONAL_HANDOFF.md`

Emplacements de code utiles :

- `src/ogn_tool/analysis/`
- `src/ogn_tool/analysis/intelligence/`
- `src/ogn_tool/reporting/`
- `apps/dashboard.py`

---

## Démarrage Rapide

Clonez le dépôt :

```bash
git clone https://github.com/HyperionXXI/ogn_tool.git
cd ogn_tool
```

Créez et activez un environnement virtuel :

```bash
python -m venv .venv
.venv\Scripts\activate
```

Installez le projet :

```bash
pip install -e .
```

Lancez l’UI actuelle :

```bash
streamlit run apps/dashboard.py
```

Ouvrez :

```text
http://localhost:8501
```

Optionnel : lancer le collecteur de paquets :

```bash
python .\scripts\collector.py
```

---

## Configuration

Exemple de `.env` :

```env
OGN_USER=CALLSIGN
OGN_PASS=PASSCODE
OGN_FILTER=r/LAT/LON/RADIUS_KM
OGN_DB_PATH=C:\path\to\ogn_log.sqlite3
OGN_HOST=glidern1.glidernet.org
OGN_PORT=14580
OGN_HOSTS=glidern1.glidernet.org,glidern2.glidernet.org,glidern3.glidernet.org,glidern5.glidernet.org
OGN_NO_PACKET_SECONDS=60
OGN_ROTATE_MINUTES=20
```

Notes :

- plusieurs analyses RF nécessitent une coverage grid remplie
- la comparaison de stations dépend de la configuration dédiée
- certaines analyses utilisent des valeurs de repli si des métadonnées station manquent

---

## Structure Du Projet

```text
apps/            UI Streamlit et points d’entrée applicatifs
scripts/         scripts runtime et utilitaires
src/ogn_tool/    package Python
docs/            architecture, contrats et documentation domaine
tests/           tests unitaires
data/            données runtime locales
```

---

## Tests

Lancer la suite de tests :

```bash
pytest
```

---

## État Du Projet

Le projet est actuellement dans une phase de **fondation d’intelligence
réseau et de reporting**.

Jalons récents :

- `v0.7-spof-detection`
- `v0.8-coverage-gap-analysis`
- `v0.9-station-addition-simulation`
- `v1.0-network-reporting-foundation`

La priorité actuelle est de stabiliser et exposer proprement le kernel
analytique, pas de faire grossir agressivement l’UI.

---

## Licence

MIT
