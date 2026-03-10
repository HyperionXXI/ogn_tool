# AGENT.md

Project: ogn_tool

Purpose:
RF network analysis platform for OGN and future RF networks.

---

# Architecture

collector  database  repositories  services  UI/API

Layers:

collector
database
repositories
analysis
services
API
UI

Dependencies must follow this direction only.

---

# Database model

tables:

packets
rf_receptions
coverage_grid
meta

Concepts:

packet = decoded protocol message
rf_reception = RF observation event

Relationship:

rf_receptions.packet_id  packets.id

---

# RF analysis rules

RF analysis modules MUST operate on:

rf_receptions

RF analysis modules MUST NOT operate on:

packets

packets are protocol data, not RF observations.

---

# SQL rules

SQL queries are allowed ONLY in:

repositories

Forbidden in:

analysis
services
UI
API

---

# UI rules

apps/dashboard.py must never query the database.

UI must call:

services layer only.

---

# Refactor policy

Refactors must:

- preserve behaviour
- not modify database schema unless explicitly requested
- not modify collector without approval
