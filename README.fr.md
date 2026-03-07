🇫🇷 Français | 🇬🇧 [English version](README.md)
# ogn_tool — Analyseur de couverture RF pour stations OGN

ogn_tool est un **outil d'analyse radio** pour les stations OGN / FLARM / FANET.
Il s'agit d'une **analyse de couverture RF pour les stations sol OGN / FLARM / FANET**.
Il permet d'enregistrer les trames radio relayées par le réseau Open Glider Network (OGN)
dans une base locale et d'explorer :
- la portée radio réelle d'une station
- les distances de réception
- les relations heard-by
- la couverture radio dans l'espace

Le projet est particulièrement utile pour :
- analyser une station OGN personnelle
- optimiser une antenne ou un site radio
- étudier la couverture FLARM / FANET locale

Analyse une base SQLite locale contenant des trames OGN/APRS-IS et
visualise la couverture et les statistiques via un tableau de bord
Streamlit.

Les sigles sont définis lors de leur première apparition et un glossaire
court est fourni plus bas.

------------------------------------------------------------------------

## Pourquoi ce projet existe

- Il existe de nombreux outils pour suivre les aéronefs.
- Il existe peu d’outils pour analyser la performance RF d’une station.
- Ce projet analyse les logs OGN pour étudier la couverture radio réelle.

------------------------------------------------------------------------

## Cas d’usage typiques

- analyse de la portée réelle d’une station
- optimisation d’une antenne
- détection de zones d’ombre dues au relief
- analyse statistique de réception
- comparaison entre stations OGN

------------------------------------------------------------------------

## Fonctionnement

-   Un **collector** se connecte à un flux TCP OGN/APRS-IS et stocke les
    trames dans une base **SQLite** (`.sqlite3`).
-   Un **dashboard** (application web Streamlit) lit cette base et
    affiche :
    -   la date de la dernière trame reçue
    -   des statistiques simples
    -   des informations de couverture et de distance
    -   une carte avec filtres (fenêtre temporelle, types de trames,
        etc.)

------------------------------------------------------------------------

## RF analysis pipeline

Le projet contient des modules d’analyse RF dans `src/ogn_tool/analysis` qui
traitent les données de couverture pour évaluer la performance RF d’une
station sol OGN :

- `signal_distance`
- `station_range`
- `station_quality`
- `polar`
- `shadow_map`
- `terrain`
- `antenna_health`
- `station_compare`
- `altitude_distance`
- `radio_horizon`

------------------------------------------------------------------------

## Chaîne radio complète

<pre>
Aircraft
   │
   │ 868 MHz
   │
émetteur FLARM / FANET
   │
   │
station sol OGN
   │
   │ Internet
   │
serveurs APRS-IS
   │
   │ flux TCP
   │
collector.py
   │
base SQLite
   │
dashboard.py
</pre>

------------------------------------------------------------------------

## Configuration (générique, recommandée)

La configuration la plus simple consiste à définir les paramètres de votre
station dans un fichier `.env` à la racine du projet. Le collector et le
dashboard le lisent automatiquement.

Exemple `.env` :

```
OGN_USER=CALLSIGN
OGN_PASS=PASSCODE
OGN_FILTER=r/LAT/LON/RADIUS_KM
OGN_DB_PATH=C:\path\to\ogn_log.sqlite3
OGN_HOST=glidern1.glidernet.org
OGN_PORT=14580
```

Notes :
- `OGN_USER` est votre callsign APRS-IS. Le dashboard l'utilise comme indicatif par défaut.
- `OGN_PASS` est le passcode APRS-IS associé.
- `OGN_FILTER` est fortement recommandé pour recevoir des données (exemple : `r/47.33/7.27/300`).

------------------------------------------------------------------------

## Démarrage rapide

### 1. Activer l'environnement Python

``` powershell
cd C:\GitHub\ogn_tool
.\.venv\Scripts\Activate.ps1
```

### 2. Définir l'emplacement de la base SQLite

Le dashboard lit le chemin de la base via une variable d'environnement :

``` powershell
$env:OGN_DB_PATH = "F:\Data\ogn\ogn_log.sqlite3"
```

### 3. Lancer le collector (Terminal 1)

Le collector doit tourner en continu pour alimenter la base SQLite.
Ouvrez un premier terminal et démarrez-le :

``` powershell
python .\scripts\collector.py
```

### 4. Lancer le dashboard (Terminal 2)

Ouvrez un second terminal (même environnement) et démarrez le dashboard :

``` powershell
streamlit run .\apps\dashboard.py
```

Une adresse locale apparaît généralement :

http://localhost:8501

------------------------------------------------------------------------

## Collector

Le collector doit tourner dans un terminal dédié en parallèle du dashboard.
Si le dashboard indique que la base semble « figée », la cause la plus
fréquente est que le collector n'est pas en cours d'exécution ou qu'il
ne peut pas joindre le flux amont.

------------------------------------------------------------------------

## Organisation du projet

-   `apps/` --- applications Streamlit (interface utilisateur)
-   `scripts/` --- scripts d'exécution comme le collector
-   `tools/` --- utilitaires (export, diagnostic, statistiques)
-   `src/ogn_tool/` --- package Python interne (configuration, accès
    base, fonctions communes)
-   `docs/` --- documentation et captures d'écran
-   `data/` --- données locales (souvent non versionnées)

------------------------------------------------------------------------

## Glossaire

-   **OGN** --- Open Glider Network, qui relaie les données FLARM/FANET via APRS.
-   **FLARM** --- système radio anticollision utilisé par les planeurs et parapentes.
-   **FANET** --- Flying Ad-hoc Network, réseau radio basse puissance pour le parapente.
-   **APRS** --- Automatic Packet Reporting System, protocole de
    communication par paquets.
-   **APRS-IS** --- APRS Internet System, distribution APRS via
    Internet.
-   **Trame / paquet** --- message reçu contenant position ou statut.
-   **SQLite** --- base de données légère stockée dans un fichier
    unique.
-   **Streamlit** --- framework Python permettant d'exécuter un tableau
    de bord web local.
-   **Indicatif (callsign)** --- identifiant d'une station (exemple :
    `FK50887`).

------------------------------------------------------------------------

## Aperçu du dashboard

![Vue générale du dashboard](docs/screenshots/dashboard_overview.png)

------------------------------------------------------------------------

## Dépannage

### Avertissement Python : invalid escape sequence

Ce message apparaît souvent lorsqu'une chaîne Python contient un
backslash (ex. `\d`).

Solutions possibles :

-   utiliser une chaîne brute : `r"...\d..."`
-   ou doubler le backslash : `"\\d"`

### Le dashboard n'affiche aucune donnée

Causes fréquentes :

-   `OGN_DB_PATH` pointe vers un mauvais fichier
-   la base ne contient pas de trames correspondant aux filtres
    sélectionnés
-   le collector n'est pas en cours d'exécution

------------------------------------------------------------------------

## Tests

``` sh
pytest
pytest tests
```

------------------------------------------------------------------------

## Données locales

`data/` contient les données locales d'exécution et n'est pas versionné dans git.
