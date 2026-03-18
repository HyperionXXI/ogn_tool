# AGENT.md

Project: ogn_tool  
Purpose: RF network analysis platform for OGN and future RF networks.

---

# Global Architecture

collector → database → repositories → analysis → pipeline → reporting → spatial → services → UI/API

Dependencies must strictly follow this direction.

No layer may bypass another.

---

# Core Principles

- Deterministic outputs
- Explicit behavior (no hidden logic)
- Stable external interfaces
- Strict separation of concerns
- Reproducibility of analysis runs

---

# Database Model

Tables:

- packets
- rf_receptions
- coverage_grid
- meta

Concepts:

packet = decoded protocol message  
rf_reception = RF observation event  

Relationship:

rf_receptions.packet_id → packets.id

---

# RF Analysis Rules

RF analysis modules MUST operate on:

- rf_receptions

RF analysis modules MUST NOT operate on:

- packets

Rationale:
packets represent protocol data, not RF signal behavior.

---

# SQL Rules

SQL queries are allowed ONLY in:

- repositories

Forbidden in:

- analysis
- pipeline
- reporting
- spatial
- services
- UI/API

---

# Pipeline Layer

Responsibilities:

- orchestrate analysis stages
- manage dataset lifecycle
- assemble intermediate artifacts

Rules:

- MUST NOT contain RF logic
- MUST NOT compute RF metrics
- MUST only coordinate execution

---

# Analysis Layer

Responsibilities:

- compute RF metrics
- produce raw quantitative outputs

Examples:

- coverage
- visibility
- antenna_pattern
- feature_matrix

Rules:

- pure computation only
- no UI logic
- no formatting
- no interpretation

---

# Network Analysis Architecture (v2)

analysis/network_metrics  
→ raw metric computation

analysis/network_metric_views  
→ qualitative interpretation

analysis/network_intelligence  
→ high-level insights

Rules:

- metrics compute only
- views interpret only
- intelligence combines multiple metrics

---

# Reporting Layer

Responsibilities:

- build NetworkEngineeringReport
- expose stable projection layer

Modules:

- reporting/report_builder.py
- reporting/report_views.py

Rules:

- MUST NOT compute metrics
- MUST consume analysis outputs only
- MUST expose stable interfaces

---

# Reporting Consumption Rules

Consumers MUST access data via:

    ogn_tool.reporting

Direct access to report internals is discouraged.

---

# Report Export Artifact

Stable external interface:

- report.json
- run_metadata.json

Rules:

- backward compatibility REQUIRED
- versioning REQUIRED (REPORT_EXPORT_VERSION)

---

# Spatial Projection Layer

Purpose:

Transform analysis or reporting data into geographic entities usable by UI systems.

Modules:

- reporting/spatial_builder.py

Rules:

- MUST NOT compute RF metrics
- MUST NOT access database
- MUST consume analysis or reporting inputs only
- MUST produce explicit diagnostics when data is missing
- MUST be deterministic and side-effect free

---

# Services Layer

Responsibilities:

- orchestrate reporting + spatial for UI/API

Rules:

- MUST NOT compute RF metrics
- MUST NOT access database directly

---

# UI Layer

Responsibilities:

- visualization only
- user interaction

Rules:

- MUST NOT access database directly
- MUST NOT compute RF metrics

---

# CLI Layer

CLI MUST remain a thin wrapper over reporting.

Allowed:

- ogn_tool.reporting

Forbidden:

- analysis
- pipeline
- runtime

---

# Run Registry

Role:

index of analysis runs only

Artifacts remain source of truth:

- report.json
- run_metadata.json

---

# Refactor Policy

Refactors MUST:

- preserve behavior
- not break exported artifacts
- not modify database schema without approval
- not modify collector without approval

---

# Swiss Engineering Quality Standard

- Deterministic behavior
- Explicit diagnostics
- No silent fallback
- Stable outputs
- Reproducibility
- Clear contracts
- Readability over cleverness

---

# Product Direction

ogn_tool is evolving into:

→ RF Network Intelligence Platform
