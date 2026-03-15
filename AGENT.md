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


# Network Analysis Architecture (v2)

The current RF/network analysis architecture is organized in layers:

analysis/network_metrics
    Computes raw network metrics from rf observations.

analysis/network_metric_views
    Converts raw metrics into qualitative engineering levels
    (confidence, redundancy, dependency, etc.).

analysis/network_intelligence
    Produces higher-level network diagnostics and derived insights.

Rules:
- network_metrics computes metrics only.
- network_metric_views interprets metrics into qualitative levels.
- network_intelligence may combine multiple metrics to derive insights.


# Pipeline Layer

The pipeline layer orchestrates the analysis workflow.

pipeline modules:
- load datasets
- execute analysis modules
- assemble metric surfaces

Pipeline modules must NOT contain RF analysis logic.


# Reporting Layer

The reporting layer projects analysis results into structured reports.

reporting modules:
- build NetworkEngineeringReport
- interpret qualitative levels from network_metric_views
- present analysis outputs in engineering form

Rules:
- reporting modules MUST NOT compute metrics
- reporting modules MUST rely on metric views or analysis outputs


# Code Quality Principles

The project follows a "Swiss engineering" coding discipline.

Rules:
- Every module must contain a top-level docstring describing its purpose.
- Public functions must include docstrings explaining parameters and design intent.
- Algorithmic thresholds must be documented with comments.
- Avoid ambiguous variable names (df, tmp, data, res).
- Code readability is preferred over compactness.

Refactors whose only purpose is readability should be avoided by writing
clear and documented code from the beginning.
