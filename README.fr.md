# ogn_tool --- Exploration locale de logs OGN / APRS-IS

Analyse une base SQLite locale contenant des trames OGN/APRS-IS et
visualise la couverture et les statistiques via un tableau de bord
Streamlit.

Les sigles sont définis lors de leur première apparition et un glossaire
court est fourni plus bas.

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

### 3. Lancer le dashboard

``` powershell
streamlit run .\apps\dashboard.py
```

Une adresse locale apparaît généralement :

http://localhost:8501

------------------------------------------------------------------------

## Collector

Pour alimenter la base SQLite :

``` powershell
python .\scripts\collector.py
```

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

-   **OGN** --- Open Glider Network, réseau communautaire de suivi.
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

## Captures d'écran

Les captures doivent être placées dans :

    docs/screenshots/

Exemple de référence une fois les images ajoutées :

``` md
![Vue générale du dashboard](docs/screenshots/dashboard_overview.png)
```

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
