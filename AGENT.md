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


Reporting consumption rules
---------------------------

Consumers of reporting data (UI, CLI, API, notebooks, dashboards) must
access report data through the stable projection layer:

    report_views

Consumers MUST use functions exposed by:

    ogn_tool.reporting

Examples:

    get_network_status(report)
    get_station_health_summary(report)
    get_network_risk_summary(report)
    get_recommended_actions(report)

Direct access to fields of NetworkEngineeringReport is discouraged.

Rationale:
The projection layer (report_views) defines a stable consumer surface.
This allows the internal structure of NetworkEngineeringReport to evolve
without breaking external consumers.


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


# Report Export Artifacts

The project defines a stable JSON export artifact derived from
NetworkEngineeringReport.

Export modules:

    reporting/report_export.py
    reporting/report_export_io.py

Responsibilities:

report_export
    Converts NetworkEngineeringReport into a stable JSON structure.

report_export_io
    Persists the JSON artifact to disk.


Architectural rules:

- report_export MUST consume report_views only.
- report_export MUST NOT read internal fields of NetworkEngineeringReport.
- report_export_io MUST consume export_network_report_json(...).
- report_export_io MUST NOT read NetworkEngineeringReport directly.


Artifact stability rules:

- The exported JSON structure is considered a stable external interface.
- The structure MUST remain backward compatible across minor versions.
- Changes to the artifact structure require incrementing REPORT_EXPORT_VERSION.


Rationale:

The JSON export artifact is intended for:

- dashboards
- notebooks
- API snapshots
- reproducible analysis archives
- comparison of network analysis runs

Maintaining a stable artifact prevents external consumers from depending
on internal report structures.


# CLI Architecture Rule

The CLI layer MUST remain a thin consumer of `ogn_tool.reporting`.

CLI code is NOT allowed to:
- read report.json directly
- read run_metadata.json directly
- read registry files directly
- rebuild comparisons
- rebuild evolution timelines
- access ogn_tool.analysis or pipeline internals

CLI commands MUST:
- call stable APIs from `ogn_tool.reporting`
- only parse arguments and format output

Allowed imports:

ogn_tool.reporting

Forbidden imports:

ogn_tool.analysis
ogn_tool.pipeline
ogn_tool.runtime
direct JSON parsing of bundles


# Run Registry Rule

The run registry is a directory index only.

The registry MUST NOT become a second data store.

Registry responsibilities:
- register run bundle locations
- list known runs
- expose stable run lookup metadata

The registry MUST NOT store:
- metrics
- analysis results
- comparisons
- derived reporting views

Analytical metadata must remain inside bundle artifacts:

    report.json
    run_metadata.json

The registry API must remain minimal:
- register_run(...)
- list_runs(...)
- load_run_metadata(...)

Rationale:
Keeping the registry as an index prevents drift toward a hidden database
layer and keeps run history architecture simple, stable and replaceable.
