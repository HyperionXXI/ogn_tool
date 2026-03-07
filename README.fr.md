🇫🇷 Français | 🇬🇧 [English version](README.md)

# ogn_tool — Analyseur de couverture RF pour stations OGN

ogn_tool est un outil d’analyse radio pour les stations
**OGN / FLARM / FANET**.

Il enregistre les trames OGN dans une base SQLite locale et permet
d’analyser les **performances radio réelles d’une station**.

---

## Fonctionnalités

- analyse polaire de couverture RF
- RSSI vs distance
- altitude vs distance
- détection de zones d’ombre radio
- estimation de portée
- diagnostic d’antenne
- estimation de l’horizon radio
- analyse du relief
- comparaison de stations
- score global de qualité

Notes :
- Plusieurs analyses RF nécessitent une coverage_grid remplie (à construire via scripts/build_coverage_grid.py).
- La comparaison de stations nécessite OGN_COMPARE_STATIONS.
- L’horizon radio utilise une altitude station par défaut de 400 m si non fournie.

---

## Pourquoi ce projet existe

De nombreux outils permettent de suivre les aéronefs.

Très peu permettent d’analyser la **performance RF des stations sol**.

ogn_tool analyse les logs OGN afin d’étudier la couverture radio réelle.

---

## Chaîne radio


```
Aircraft
│
│ 868 MHz
│
émetteur FLARM / FANET
│
station sol OGN
│
Internet
│
serveurs APRS-IS
│
collector.py
│
base SQLite
│
modules d’analyse RF
│
dashboard.py
```


---

## Démarrage rapide

```bash
git clone https://github.com/HyperionXXI/ogn_tool.git
cd ogn_tool
python -m venv .venv
.venv\Scripts\activate
pip install -e .
streamlit run apps/dashboard.py
```

Optionnel (collector):

```bash
python .\scripts\collector.py
```

---

## Configuration

Exemple .env:

```
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

---

## Structure du projet

```
apps/
scripts/
tools/
src/ogn_tool/
docs/
tests/
data/
```

---

## Tests

```bash
pytest
```

---

## Licence

MIT
