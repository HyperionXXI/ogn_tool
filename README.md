🇬🇧 English | 🇫🇷 [Version française](README.fr.md)

# ogn_tool --- Local OGN / APRS-IS log explorer

ogn_tool is a **radio analysis tool** for OGN / FLARM / FANET stations.
It records radio frames relayed by the Open Glider Network (OGN) into a local
database and lets you explore:
- the real-world reception range of a station
- reception distances
- heard-by relationships
- radio coverage in space

The project is especially useful to:
- analyze your own OGN station
- optimize an antenna or radio site
- study local FLARM / FANET coverage

Analyze a local SQLite log database containing OGN/APRS-IS packets and
visualize coverage and statistics with a Streamlit dashboard.

Most acronyms are defined the first time they appear. A short glossary
is also provided below.

------------------------------------------------------------------------

## What it does

-   A **collector** connects to an OGN/APRS-IS TCP feed and stores
    packets into a local **SQLite** database file (`.sqlite3`).
-   A **dashboard** (Streamlit web app) reads that database and shows:
    -   last packet time and packet counts
    -   basic health indicators
    -   coverage and distance statistics
    -   map views and filters (time window, packet types, etc.)

------------------------------------------------------------------------

## Radio chain (end-to-end)

<pre>
Aircraft
   │
   │ 868 MHz
   │
FLARM / FANET transmitter
   │
   │
OGN ground station
   │
   │ Internet
   │
APRS-IS servers
   │
   │ TCP stream
   │
collector.py
   │
SQLite database
   │
dashboard.py
</pre>

------------------------------------------------------------------------

## Configuration (generic, recommended)

The simplest setup is to define your station settings in a local `.env`
file at the project root. Both the collector and the dashboard will read it.

Example `.env`:

```
OGN_USER=CALLSIGN
OGN_PASS=PASSCODE
OGN_FILTER=r/LAT/LON/RADIUS_KM
OGN_DB_PATH=C:\path\to\ogn_log.sqlite3
OGN_HOST=glidern1.glidernet.org
OGN_PORT=14580
```

Notes:
- `OGN_USER` is your APRS-IS callsign. The dashboard uses it as default station callsign.
- `OGN_PASS` is the APRS-IS passcode for that callsign.
- `OGN_FILTER` is strongly recommended to receive data (example: `r/47.33/7.27/300`).

------------------------------------------------------------------------

## Quickstart

### 1. Activate the Python environment

``` powershell
cd C:\GitHub\ogn_tool
.\.venv\Scripts\Activate.ps1
```

### 2. Define the SQLite database location

The dashboard reads the database path from an environment variable:

``` powershell
$env:OGN_DB_PATH = "F:\Data\ogn\ogn_log.sqlite3"
```

### 3. Run the collector (Terminal 1)

The collector must run continuously to populate the SQLite database.
Open a first terminal and start it:

``` powershell
python .\scripts\collector.py
```

### 4. Run the dashboard (Terminal 2)

Open a second terminal (same environment) and start the dashboard:

``` powershell
streamlit run .\apps\dashboard.py
```

A local address will appear, typically:

http://localhost:8501

------------------------------------------------------------------------

## Collector

The collector should run in its own terminal alongside the dashboard.
If the dashboard reports that the database appears "stale" or "frozen",
the most common reason is that the collector is not currently running or
cannot reach the upstream feed.

------------------------------------------------------------------------

## Project layout

-   `apps/` --- Streamlit applications (user interface)
-   `scripts/` --- runtime scripts such as the collector
-   `tools/` --- utility scripts (exports, diagnostics, statistics)
-   `src/ogn_tool/` --- internal Python package (configuration, database
    access, shared code)
-   `docs/` --- documentation and screenshots
-   `data/` --- local data (usually not versioned)

------------------------------------------------------------------------

## Glossary

-   **OGN** --- Open Glider Network, which relays FLARM/FANET data via APRS.
-   **FLARM** --- collision-avoidance radio system used by gliders and paragliders.
-   **FANET** --- Flying Ad-hoc Network, a low-power radio network used in paragliding.
-   **APRS** --- Automatic Packet Reporting System, a packet
    communication protocol.
-   **APRS-IS** --- APRS Internet System, APRS data distributed via
    internet servers.
-   **Packet / frame** --- a received message containing position or
    status data.
-   **SQLite** --- a lightweight database stored in a single file.
-   **Streamlit** --- a Python framework used to run a local web
    dashboard.
-   **Callsign** --- a station identifier (example: `FK50887`).

------------------------------------------------------------------------

## Screenshots

Screenshots should be placed in:

    docs/screenshots/

Example reference once images exist:

``` md
![Dashboard overview](docs/screenshots/dashboard_overview.png)
```

------------------------------------------------------------------------

## Troubleshooting

### SyntaxWarning: invalid escape sequence

This warning usually comes from Python strings containing backslashes
(such as `\d`).

Possible fixes:

-   use a raw string: `r"...\d..."`
-   or escape the backslash: `"\\d"`

### Dashboard shows no data

Common causes:

-   `OGN_DB_PATH` points to the wrong database file
-   the database contains no packets matching the selected filters
-   the collector is not running

------------------------------------------------------------------------

## Tests

``` sh
pytest
pytest tests
```

------------------------------------------------------------------------

## Local data

`data/` contains local runtime data and is not versioned in git.
