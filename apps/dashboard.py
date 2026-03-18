#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OGN Tool — Spatial RF Network Explorer (Product Layer)

This dashboard intentionally contains:
- No database access
- No analysis logic
- No pipeline execution

It only renders an explorable, map-centric UI from an input report by using
`ogn_tool.reporting.ui_projection.build_ui_projection`.

Run:
  streamlit run .\\apps\\dashboard.py

Optional env:
  OGN_REPORT_PATH=/path/to/report.json
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import pydeck as pdk
import streamlit as st

from ogn_tool.reporting.ui_projection import build_ui_projection


st.set_page_config(page_title="OGN Tool — Spatial Explorer", layout="wide")


def _load_report_from_path(path: str) -> Optional[Dict[str, Any]]:
    if not path:
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _load_report_from_upload(upload) -> Optional[Dict[str, Any]]:
    if upload is None:
        return None
    try:
        return json.loads(upload.read().decode("utf-8"))
    except Exception:
        return None


def _safe_float(x) -> Optional[float]:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def _center_from_points(points: List[Dict[str, Any]]) -> Tuple[float, float]:
    lat = [_safe_float(p.get("lat")) for p in points]
    lon = [_safe_float(p.get("lon")) for p in points]
    lat = [v for v in lat if v is not None]
    lon = [v for v in lon if v is not None]
    if not lat or not lon:
        return 47.3359, 7.2728  # benign default
    return float(sum(lat) / len(lat)), float(sum(lon) / len(lon))


def _coerce_points(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        lat = _safe_float(it.get("lat"))
        lon = _safe_float(it.get("lon"))
        if lat is None or lon is None:
            continue
        out.append({**it, "lat": lat, "lon": lon})
    return out


st.title("Spatial RF Network Explorer")
st.caption("Load a report and explore the network spatially (stations, links, coverage, blind zones, risks).")

with st.sidebar:
    st.markdown("## Data")
    default_path = os.getenv("OGN_REPORT_PATH", "")
    report_path = st.text_input("Report JSON path (optional)", value=default_path)
    uploaded = st.file_uploader("…or upload `report.json`", type=["json"])
    st.markdown("## Layers")
    show_links = st.checkbox("Links", value=True)
    show_coverage = st.checkbox("Coverage", value=True)
    show_blind = st.checkbox("Blind zones", value=True)
    show_risk = st.checkbox("Risk zones", value=True)


report: Optional[Dict[str, Any]] = None
if uploaded is not None:
    report = _load_report_from_upload(uploaded)
elif report_path:
    report = _load_report_from_path(report_path)

if report is None:
    st.info("Provide a report (`report.json`) to begin.")
    st.stop()

projection = build_ui_projection(report)

stations = _coerce_points(projection.get("stations", []))
coverage = _coerce_points(projection.get("coverage", []))
blind = _coerce_points(projection.get("blind_zones", []))
risk = _coerce_points(projection.get("risk_zones", []))

center_lat, center_lon = _center_from_points(stations or coverage or risk or blind)

layers: List[pdk.Layer] = []

if stations:
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            stations,
            get_position="[lon, lat]",
            get_radius=150,
            get_fill_color=[40, 120, 255, 190],
            pickable=True,
        )
    )

if show_risk and risk:
    def _risk_color(r):
        level = str(r.get("risk") or "").lower()
        if level == "critical":
            return [255, 60, 60, 200]
        if level == "warning":
            return [255, 170, 0, 190]
        return [180, 180, 180, 160]

    for r in risk:
        r["__color"] = _risk_color(r)

    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            risk,
            get_position="[lon, lat]",
            get_radius=220,
            get_fill_color="__color",
            pickable=True,
        )
    )

if show_coverage and coverage:
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            coverage,
            get_position="[lon, lat]",
            get_radius=120,
            get_fill_color=[0, 200, 120, 90],
            pickable=False,
        )
    )

if show_blind and blind:
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            blind,
            get_position="[lon, lat]",
            get_radius=160,
            get_fill_color=[120, 120, 120, 90],
            pickable=False,
        )
    )

if show_links and projection.get("links"):
    station_index = {str(s.get("station_id")): s for s in stations if s.get("station_id") is not None}
    paths = []
    for e in projection["links"]:
        if not isinstance(e, dict):
            continue
        src = str(e.get("source") or "")
        dst = str(e.get("target") or "")
        a = station_index.get(src)
        b = station_index.get(dst)
        if not a or not b:
            continue
        paths.append(
            {
                "path": [[a["lon"], a["lat"]], [b["lon"], b["lat"]]],
                "kind": e.get("type") or e.get("kind"),
            }
        )
    if paths:
        layers.append(
            pdk.Layer(
                "PathLayer",
                paths,
                get_path="path",
                get_width=3,
                get_color=[160, 160, 160],
                pickable=False,
            )
        )

view_state = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=8, pitch=0)
deck = pdk.Deck(
    layers=layers,
    initial_view_state=view_state,
    tooltip={"text": "{station_id}\n{health_status}\n{risk}"},
)

col_map, col_inspector = st.columns([0.72, 0.28], gap="large")
with col_map:
    st.pydeck_chart(deck, use_container_width=True, height=780)

with col_inspector:
    st.markdown("### Inspector")
    st.caption("This panel will evolve into an entity/relationship explorer.")
    st.markdown("**Counts**")
    st.write(
        {
            "stations": len(projection.get("stations", [])),
            "links": len(projection.get("links", [])),
            "coverage": len(projection.get("coverage", [])),
            "blind_zones": len(projection.get("blind_zones", [])),
            "risk_zones": len(projection.get("risk_zones", [])),
        }
    )
    with st.expander("Projection preview"):
        st.json(projection)











