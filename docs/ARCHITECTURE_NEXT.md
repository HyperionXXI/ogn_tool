# Architecture Next

This document describes the future target architecture for `ogn_tool` while
preserving the current Streamlit UI and RF analysis engine.

## Goal

Prepare the codebase for a React + FastAPI architecture without breaking
existing functionality. The current Streamlit dashboard remains the active UI.

## Target Architecture

collector
→ database (SQLite now, extensible later)
→ analysis + engine
→ API (FastAPI)
→ frontend (React)

### Layers

- Collector
  Ingests APRS/OGN packets and stores them in the database.

- Database
  Source of truth for packets, receptions, and derived RF datasets.

- Analysis / Engine
  RFAnalysisEngine orchestrates analysis modules and produces datasets.

- API (FastAPI)
  Future public interface for datasets and RF intelligence services.

- Frontend (React)
  Future visualization layer consuming API endpoints.

## Current State

- Streamlit dashboard is the active UI.
- RF analysis runs in `RFAnalysisEngine`.
- Database access is being centralized in repository modules.
- Service layer is introduced as a thin integration boundary.

## Migration Principles

- Do not break existing Streamlit UI.
- Keep analysis logic in the engine and analysis modules.
- Move SQL access into repository modules.
- Introduce service layer for API and UI reuse.
- Add API skeleton without changing data flow.
