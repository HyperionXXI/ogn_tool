🇬🇧 English | 🇫🇷 [Version française](README.fr.md)

# ogn_tool — RF Coverage Analyzer

RF coverage analysis tool for **OGN / FLARM / FANET ground stations**.

ogn_tool records packets from the Open Glider Network (OGN) into a
local SQLite database and provides RF diagnostics using a Streamlit
dashboard.

The goal is to analyze the **real-world RF performance of a ground station**.

---

## Features

- Polar RF coverage analysis
- RSSI vs distance
- Altitude vs distance
- Radio shadow detection
- Station range estimation
- Antenna diagnostics
- Radio horizon analysis
- Terrain limitation detection
- Multi-station comparison
- Global station quality score

Notes:
- Several RF analyses require a populated coverage_grid (build it with scripts/build_coverage_grid.py).
- Station comparison requires OGN_COMPARE_STATIONS to be configured.
- Radio horizon uses a fallback station altitude of 400 m if not provided.

---

## Why this project exists

Many tools exist to track aircraft positions.

Very few tools analyze the **RF performance of ground stations**.

ogn_tool analyzes OGN logs to study real-world radio coverage.

---

## Radio chain

```
Aircraft
│
│ 868 MHz
│
FLARM / FANET transmitter
│
OGN ground station
│
Internet
│
APRS-IS servers
│
collector.py
│
SQLite database
│
RF analysis modules
│
dashboard.py
```


---

## RF analysis modules

Located in:

`src/ogn_tool/analysis`

Modules:

- signal_distance
- station_range
- station_quality
- polar
- shadow_map
- terrain
- antenna_health
- station_compare
- altitude_distance
- radio_horizon

---

## Quick start

Clone the repository:

```bash
git clone https://github.com/HyperionXXI/ogn_tool.git
cd ogn_tool
```

Create environment:

```bash
python -m venv .venv
```

Activate:

```bash
.venv\Scripts\activate
```

Install:

```bash
pip install -e .
```

Run dashboard:

```bash
streamlit run apps/dashboard.py
```

Open:

http://localhost:8501

Optional (collector):

```bash
python .\scripts\collector.py
```

---

## Configuration

Example .env:

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

## Project structure

```
apps/            Streamlit dashboard
scripts/         runtime scripts
tools/           utilities
src/ogn_tool/    Python package
docs/            documentation
data/            local runtime data
tests/           unit tests
```

---

## Troubleshooting

### Dashboard shows no data

Possible causes:

- collector not running
- wrong database path
- filters excluding packets

---

## Tests

```bash
pytest
```

---

## License

MIT License


---
