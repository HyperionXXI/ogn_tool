🇬🇧 English | 🇫🇷 [Version française](README.fr.md)

# ogn_tool — RF Network Intelligence Engine
for OGN / FLARM / FANET ground-station networks

An open-source engine for analyzing, diagnosing, and planning
distributed RF observation networks.

`ogn_tool` is an RF analysis and network intelligence toolkit for
**OGN / FLARM / FANET ground-station networks**.

It started as a station-centric RF coverage analyzer and has evolved
into a layered analytical engine that can:

- analyze real RF observations
- diagnose station and network weaknesses
- simulate network failure scenarios
- prioritize coverage and redundancy improvements
- assemble operator-facing network engineering reports

The current Streamlit dashboard is a consumer UI. It is not the core
product.

---

## Why This Project Exists

Many tools can display aircraft positions.

Far fewer tools help answer engineering questions about the RF
observation network itself.

`ogn_tool` exists to analyze the real behavior of RF observation
networks and turn raw reception data into actionable decisions such as:

- which station is weak
- which station is critical
- where coverage is insufficient
- where redundancy should be added
- what improvement a new station could bring

The project therefore targets not only visualization, but also
**diagnosis, reasoning, and planning** for distributed RF networks.

It is not just another tracker UI. It is the analytical layer behind
RF network understanding and decision-making.

The architecture is protocol-agnostic and can analyze other RF
observation networks beyond the current OGN / FLARM / FANET focus.

---

## Who Is This For?

This project is primarily intended for:

- OGN station operators
- RF network engineers
- free-flight infrastructure builders
- research groups studying RF coverage and observation networks

---

## Terminology

In this repository, the following terms have strict meanings:

- `analysis`: computes measurable RF or network facts
- `intelligence`: derives actionable diagnostics, priorities, and
  scenarios from analytical outputs
- `reporting`: assembles operator-facing summaries from typed runtime
  results
- `UI`: displays, filters, and formats results without recomputing them
- `results.*`: official typed runtime API exposed to downstream
  consumers

### Domain Glossary

- `OGN`: Open Glider Network, a distributed network that collects and
  shares aircraft tracking and reception data
- `FLARM`: a collision-warning and tracking system widely used in
  gliders and light aircraft
- `FANET`: Flying Ad-hoc Network, a lightweight airborne mesh-oriented
  radio protocol used notably in free-flight ecosystems
- `APRS`: Automatic Packet Reporting System, a packet-based reporting
  network used for position and telemetry exchange
- `APRS-IS`: the internet-connected APRS server network used to relay
  APRS traffic
- `RF`: radio frequency
- `SPOF`: single point of failure
- `RSSI`: received signal strength indicator
- `UI`: user interface

---

## What The Project Does

At a high level, `ogn_tool` helps answer questions such as:

- How well is a station performing in real-world conditions?
- Which stations are critical to the network?
- Where are the network coverage gaps?
- What happens if a station disappears?
- Where should redundancy be added first?
- Which candidate location could improve the network?

This makes the project useful both for **RF diagnostics** and for
**network engineering**.

---

## Architecture In One View

The project is organized as a layered system:

```text
ingestion
  -> normalization
  -> analysis
  -> intelligence
  -> reporting
  -> UI
```

Responsibilities:

- `analysis`: computes measurable RF and network metrics
- `intelligence`: derives actionable diagnostics and scenarios
- `reporting`: assembles operator-facing summaries
- `apps/ui`: visualizes results

The official runtime surface is `results.*`, especially
`results.network_metrics`.

---

## Current Capabilities

### RF diagnostics

- polar coverage analysis
- RSSI vs distance analysis
- altitude vs distance analysis
- radio shadow detection
- station range estimation
- antenna diagnostics
- radio horizon analysis
- terrain limitation analysis
- multi-station comparison

### Network intelligence

- station health diagnostics
- network summary
- station dependency analysis
- single point of failure detection
- station removal simulation
- station redundancy planning
- coverage gap detection
- coverage gap prioritization
- empirical station addition simulation

### Reporting

- typed network engineering report builder
- reporting layer built on typed runtime results

---

## Repository Entry Points

If you are new to the repository, start here:

- `README.md`
- `docs/ARCHITECTURE.md`
- `docs/architecture/INDEX.md`
- `docs/architecture/OPERATIONAL_HANDOFF.md`

Useful code locations:

- `src/ogn_tool/analysis/`
- `src/ogn_tool/analysis/intelligence/`
- `src/ogn_tool/reporting/`
- `apps/dashboard.py`

---

## Quick Start

Clone the repository:

```bash
git clone https://github.com/HyperionXXI/ogn_tool.git
cd ogn_tool
```

Create and activate a virtual environment:

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install the project:

```bash
pip install -e .
```

Run the current dashboard UI:

```bash
streamlit run apps/dashboard.py
```

Open:

```text
http://localhost:8501
```

Optional: run the packet collector:

```bash
python .\scripts\collector.py
```

---

## Configuration

Example `.env`:

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

Notes:

- several RF analyses require a populated coverage grid
- station comparison requires the relevant comparison configuration
- some analyses use fallback defaults when station metadata is missing

---

## Project Structure

```text
apps/            Streamlit UI and app entry points
scripts/         runtime and utility scripts
src/ogn_tool/    Python package
docs/            architecture, contracts, and domain documentation
tests/           unit tests
data/            local runtime data
```

---

## Tests

Run the test suite:

```bash
pytest
```

---

## Project Status

The project is currently in a **network intelligence and reporting
foundation** phase.

Recent milestones include:

- `v0.7-spof-detection`
- `v0.8-coverage-gap-analysis`
- `v0.9-station-addition-simulation`
- `v1.0-network-reporting-foundation`

The current priority is to stabilize and expose the analytical kernel,
not to grow the UI aggressively.

---

## License

MIT License
