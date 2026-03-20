#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OGN Tool - Spatial RF Network Explorer (Product Layer)

Dashboard v2 constraints:
- No database access
- No analysis logic
- No pipeline execution
- UI consumes reporting views/contracts only
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

import pydeck as pdk
import streamlit as st

from ogn_tool.reporting.views.dashboard_views import (
    build_dashboard_payload,
    load_report_from_path,
    load_report_from_upload,
)


st.set_page_config(page_title="OGN Tool - Spatial Explorer", layout="wide")


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
        return 47.3359, 7.2728
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


@st.cache_data
def _load_payload_from_path(path: str) -> Optional[Dict[str, Any]]:
    report = load_report_from_path(path)
    if report is None:
        return None
    return build_dashboard_payload(report)


@st.cache_data
def _load_payload_from_bytes(raw: bytes) -> Optional[Dict[str, Any]]:
    class _UploadShim:
        def __init__(self, payload: bytes):
            self._payload = payload

        def read(self) -> bytes:
            return self._payload

    report = load_report_from_upload(_UploadShim(raw))
    if report is None:
        return None
    return build_dashboard_payload(report)


st.title("Spatial RF Network Explorer")
st.caption("Load a report and explore the network spatially (stations, links, coverage, blind zones, risks).")

with st.sidebar:
    st.markdown("## Data")
    default_path = os.getenv("OGN_REPORT_PATH", "")
    report_path = st.text_input("Report JSON path (optional)", value=default_path)
    uploaded = st.file_uploader("...or upload `report.json`", type=["json"])

    st.markdown("## Layers")
    show_links = st.checkbox("Links", value=True)
    show_coverage = st.checkbox("Coverage", value=True)
    show_blind = st.checkbox("Blind zones", value=True)
    show_risk = st.checkbox("Risk zones", value=True)

payload: Optional[Dict[str, Any]] = None
if uploaded is not None:
    payload = _load_payload_from_bytes(uploaded.getvalue())
elif report_path:
    payload = _load_payload_from_path(report_path)

if payload is None:
    st.info("Provide a report (`report.json`) to begin.")
    st.stop()

projection = payload.get("metrics", {})
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
        paths.append({"path": [[a["lon"], a["lat"]], [b["lon"], b["lat"]]], "kind": e.get("type") or e.get("kind")})
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
deck = pdk.Deck(layers=layers, initial_view_state=view_state, tooltip={"text": "{station_id}\n{health_status}\n{risk}"})

col_map, col_inspector = st.columns([0.72, 0.28], gap="large")
with col_map:
    st.pydeck_chart(deck, use_container_width=True, height=780)

with col_inspector:
    st.markdown("### Inspector")
    st.caption("Projection-only panel fed by reporting views.")

    summary = payload.get("network_summary", {})
    st.metric("Stations", summary.get("station_count") or 0)
    st.metric("Packet count", summary.get("packet_count") or 0)

    if not payload.get("stations"):
        st.info("No stations available for this dataset")

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

    st.subheader("RF Coverage Signature")
    rf = payload.get("intelligence", {}).get("rf_analysis", {})
    sig = rf.get("rf_signature", {}) if isinstance(rf, dict) else {}

    if not sig:
        st.info("RF signature unavailable (insufficient station data)")
    else:
        coverage_bins = sig.get("azimuth_coverage", [])
        dominant = sig.get("dominant_directions", [])
        uniformity = sig.get("coverage_uniformity_score")

        st.write("Azimuth coverage (360°)")
        for i, value in enumerate(coverage_bins):
            numeric_value = _safe_float(value)
            if numeric_value is None:
                continue
            bounded = min(1.0, max(0.0, numeric_value))
            angle = i * 30
            st.progress(bounded)
            st.caption(f"{angle}° - {bounded:.2f}")

        if isinstance(dominant, list) and dominant:
            dirs = ", ".join(f"{int(d)}°" for d in dominant if _safe_float(d) is not None)
            st.write(f"Dominant directions: {dirs}" if dirs else "Dominant directions: none")
        else:
            st.write("Dominant directions: none")

        uniformity_value = _safe_float(uniformity)
        if uniformity_value is not None:
            st.write(f"Coverage uniformity: {uniformity_value:.2f}")
            if uniformity_value > 0.75:
                st.success("Uniform coverage")
            elif uniformity_value > 0.5:
                st.warning("Moderately directional coverage")
            else:
                st.error("Strong directional bias (possible terrain shadowing)")

        gaps = rf.get("rf_directional_gaps", {}) if isinstance(rf, dict) else {}
        if isinstance(gaps, dict) and gaps:
            gap_angles = gaps.get("gaps", [])
            if isinstance(gap_angles, list) and gap_angles:
                st.write("Coverage gaps:", ", ".join(f"{int(g)}°" for g in gap_angles if _safe_float(g) is not None))
                severity = str(gaps.get("severity") or "").lower()
                if severity == "high":
                    st.error("Severe directional coverage gaps")
                elif severity == "medium":
                    st.warning("Moderate directional gaps")
                else:
                    st.info("Minor directional gaps")

    with st.expander("Debug"):
        st.json(payload.get("debug", {}))
