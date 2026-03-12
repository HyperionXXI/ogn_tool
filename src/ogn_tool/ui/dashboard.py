#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
OGN / APRS-IS — Dashboard local (SQLite)

Objectives:
- Clear UI (wide), no regression (map + signal-vs-distance when data available)
- Robust to small schema variations (missing columns)
- "Coverage" = packets heard-by your station (igate=FK50887 or raw contains ",FK50887:")
- Performance: time window + SQL row limit + cache TTL

Run:
  streamlit run .\dashboard.py
"""

from __future__ import annotations

import datetime as dt
import cProfile
import io
import hashlib
import json
import math
import os
import re
import time
import pstats
from dataclasses import dataclass, replace
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st
try:
    import plotly.graph_objects as go
except Exception:  # pragma: no cover
    go = None

from ogn_tool.ui.layout import DASHBOARD_COLUMNS
from apps.ui.metrics import metric_card
from ogn_tool.ui.filters import render_sidebar_filters
from ogn_tool.ui.sections import (
    render_overview_tab,
    render_coverage_explorer_tab,
    render_signal_tab,
    render_network_tab,
    render_diagnostics_tab,
    render_station_intelligence_tab,
    render_network_intelligence_tab,
)

from ogn_tool.config import get_config
from ogn_tool.data.db_repository import db_meta as repo_db_meta, db_max_ts_epoch as repo_db_max_ts_epoch, optimize_db as repo_optimize_db, create_indexes as repo_create_indexes, rf_sanity_check as repo_rf_sanity_check, table_exists_db
from ogn_tool.data.packets_repository import load_packets_window
from ogn_tool.data.receptions_repository import load_rf_receptions
from ogn_tool.engine.rf_engine import RFAnalysisEngine


# Optional profiling (enable with OGN_PROFILE=1)
_PROFILE_ENABLED = os.getenv("OGN_PROFILE", "0") in ("1", "true", "True")
_PROFILER = cProfile.Profile() if _PROFILE_ENABLED else None
if _PROFILER:
    try:
        _PROFILER.enable()
    except ValueError:
        _PROFILER = None

# ---------------------------
# Config & helpers
# ---------------------------

st.set_page_config(
    page_title="OGN RF Intelligence",
    layout="wide",
    page_icon="📡",
)

# Global styling
st.markdown(
    """
<style>
[data-testid="stMetricValue"] { font-size: 30px; }
[data-testid="stMetricLabel"] { font-size: 14px; }
section[data-testid="stSidebar"] { width: 320px !important; }
</style>
""",
    unsafe_allow_html=True,
)


_config = get_config()
DB_DEFAULT = str(_config.db_path)
CALLSIGN_DEFAULT = _config.station_callsign
# Reference location provided (Google Maps)
ROOF_LAT_DEFAULT = 47.33593787391701
ROOF_LON_DEFAULT = 7.272825467967339

RE_DB = re.compile(r"(?P<db>\d+(?:\.\d+)?)\s*dB\b")


@dataclass(frozen=True)
class Basemap:
    name: str
    tiles: str
    attr: str


BASEMAPS: Dict[str, Basemap] = {
    "OpenStreetMap (standard)": Basemap(
        name="OpenStreetMap (standard)",
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr="© OpenStreetMap contributors",
    ),
    "CARTO Positron (clair)": Basemap(
        name="CARTO Positron (clair)",
        tiles="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
        attr="© CARTO © OpenStreetMap contributors",
    ),
    "CARTO Dark Matter (dark)": Basemap(
        name="CARTO Dark Matter (dark)",
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="© CARTO © OpenStreetMap contributors",
    ),
}

DEFAULT_BASEMAP = "CARTO Positron (clair)"


def haversine_km(lat1: float, lon1: float, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    """Vectorized haversine distance in km."""
    r = 6371.0
    lat1r = np.deg2rad(lat1)
    lon1r = np.deg2rad(lon1)
    lat2r = np.deg2rad(lat2.astype(float))
    lon2r = np.deg2rad(lon2.astype(float))
    dlat = lat2r - lat1r
    dlon = lon2r - lon1r
    a = np.sin(dlat / 2.0) ** 2 + np.cos(lat1r) * np.cos(lat2r) * np.sin(dlon / 2.0) ** 2
    c = 2.0 * np.arcsin(np.sqrt(a))
    return r * c




def safe_col(df: pd.DataFrame, col: str, default=None) -> pd.Series:
    if col in df.columns:
        return df[col]
    return pd.Series([default] * len(df), index=df.index)


def parse_db_from_raw(raw: str) -> Optional[float]:
    if not isinstance(raw, str):
        return None
    m = RE_DB.search(raw)
    if not m:
        return None
    try:
        return float(m.group("db"))
    except Exception:
        return None


def fmt_int(n: Optional[int]) -> str:
    if n is None:
        return "—"
    return f"{n:,}".replace(",", "'")


def fmt_float(x: Optional[float], nd: int = 1) -> str:
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return "—"
    try:
        x = float(x)
    except (TypeError, ValueError):
        return "—"
    return f"{x:.{nd}f}"


def first_valid_df(*dfs):
    """Return the first DataFrame that is not None and not empty."""
    for df in dfs:
        if isinstance(df, pd.DataFrame) and not df.empty:
            return df
    return pd.DataFrame()


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def _parse_compare_stations(env_value: str) -> Dict[str, Tuple[float, float]]:
    stations: Dict[str, Tuple[float, float]] = {}
    if not env_value:
        return stations
    for item in env_value.split(";"):
        item = item.strip()
        if not item or ":" not in item:
            continue
        callsign, coords = item.split(":", 1)
        callsign = callsign.strip()
        if not callsign or "," not in coords:
            continue
        lat_s, lon_s = coords.split(",", 1)
        try:
            stations[callsign] = (float(lat_s.strip()), float(lon_s.strip()))
        except ValueError:
            continue
    return stations


# ---------------------------
# DB layer
# ---------------------------

def _db_meta_raw(db_path: str, query_log: Optional[List[Dict]] = None) -> Tuple[int, Optional[str]]:
    return repo_db_meta(db_path, query_log=query_log)


@st.cache_data(ttl=30, show_spinner=False)
def db_meta(db_path: str) -> Tuple[int, Optional[str]]:
    return _db_meta_raw(db_path)


@st.cache_data(ttl=30, show_spinner=False)
def db_max_ts_epoch(db_path: str) -> Optional[int]:
    return repo_db_max_ts_epoch(db_path)

def optimize_db(db_path: str, vacuum: bool = False) -> None:
    repo_optimize_db(db_path, vacuum=vacuum)

def _set_query_ts(ts: str) -> None:
    # Streamlit API compatibility
    if hasattr(st, "query_params"):
        st.query_params["_ts"] = ts
    elif hasattr(st, "set_query_params"):
        st.set_query_params(_ts=ts)
    elif hasattr(st, "experimental_set_query_params"):
        st.experimental_set_query_params(_ts=ts)

def _autorefresh(interval_ms: int, key: str) -> None:
    if hasattr(st, "autorefresh"):
        st.autorefresh(interval=interval_ms, key=key)
    else:
        # Fallback: simple cache-busting query param to trigger rerun
        _set_query_ts(str(int(dt.datetime.now().timestamp())))

def create_indexes(db_path: str) -> None:
    repo_create_indexes(db_path)

def rf_sanity_check(db_path: str) -> List[str]:
    return repo_rf_sanity_check(db_path)

@st.cache_data(ttl=5, show_spinner=False)
@st.cache_data(show_spinner=False)
def _load_packets_window_raw(
    db_path: str,
    since_iso: str,
    since_epoch: int,
    dst_types: List[str],
    station_callsign: str,
    only_heard_by: bool,
    igate_filter: str,
    source_mode: str,
    qas_filter: str,
    limit_rows: int,
    query_log: Optional[List[Dict]] = None,
) -> pd.DataFrame:
    if not os.path.exists(db_path):
        return pd.DataFrame()

    df = load_packets_window(
        db_path=db_path,
        since_iso=since_iso,
        since_epoch=since_epoch,
        dst_types=dst_types,
        station_callsign=station_callsign,
        only_heard_by=only_heard_by,
        igate_filter=igate_filter,
        source_mode=source_mode,
        qas_filter=qas_filter,
        limit_rows=limit_rows,
        query_log=query_log,
    )

    # Optional diagnostics for timestamp filtering (enable with OGN_DEBUG=1)
    if os.getenv("OGN_DEBUG", "0") in ("1", "true", "True"):
        try:
            print("[debug] timestamp columns:", list(df.columns))
            if "timestamp" in df.columns:
                print("[debug] min timestamp:", df["timestamp"].min(), "max timestamp:", df["timestamp"].max())
            if "ts_epoch" in df.columns:
                print("[debug] min ts_epoch:", df["ts_epoch"].min(), "max ts_epoch:", df["ts_epoch"].max())
            print("[debug] cutoff epoch:", since_epoch)
            if "raw" in df.columns:
                print("[debug] qAR count:", df["raw"].str.contains("qAR", na=False, regex=False).sum())
                print("[debug] qAO count:", df["raw"].str.contains("qAO", na=False, regex=False).sum())
                print("[debug] qAC count:", df["raw"].str.contains("qAC", na=False, regex=False).sum())
                print("[debug] example packets:")
                print(df["raw"].head(5))
            print("[debug] columns:", list(df.columns))
            if "igate" in df.columns:
                print("[debug] igate values:")
                print(df["igate"].value_counts().head(20))
            if "qas" in df.columns:
                print("[debug] qas values:")
                print(df["qas"].value_counts())
                print("[debug] qAR count (qas):", (df["qas"] == "qAR").sum())
                print("[debug] qAO count (qas):", (df["qas"] == "qAO").sum())
            if "raw" in df.columns:
                station = str(station_callsign).upper()
                print("[debug] packets containing station:")
                print(df[df["raw"].str.contains(station, na=False, regex=False)].head())
                print("[debug] station count:", df["raw"].str.contains(station, na=False, regex=False).sum())
        except Exception as e:
            print("[debug] timestamp diagnostics failed:", repr(e))

    return df


@st.cache_data(show_spinner=False)
def _load_rf_receptions_window_raw(
    db_path: str,
    since_epoch: int,
    limit_rows: int,
    station_id: str,
    query_log: Optional[List[Dict]] = None,
) -> pd.DataFrame:
    if not os.path.exists(db_path):
        return pd.DataFrame()

    return load_rf_receptions(
        db_path=db_path,
        since_epoch=since_epoch,
        limit_rows=limit_rows,
        station_id=station_id,
        query_log=query_log,
    )


# ---------------------------
# Derived computations
# ---------------------------

@st.cache_data(show_spinner=False)
def compute_features(df: pd.DataFrame, station_lat: float, station_lon: float) -> pd.DataFrame:
    if df.empty:
        out = df.copy()
        out["rx_db"] = pd.Series(dtype=float)
        out["distance_km"] = pd.Series(dtype=float)
        return out

    out = df.copy()
    out["lat"] = pd.to_numeric(safe_col(out, "lat"), errors="coerce")
    out["lon"] = pd.to_numeric(safe_col(out, "lon"), errors="coerce")

    # Fast vectorized dB parse
    raw_series = safe_col(out, "raw").astype("string")
    out["rx_db"] = pd.to_numeric(raw_series.str.extract(RE_DB, expand=False), errors="coerce")

    mask_ll = out["lat"].notna() & out["lon"].notna()
    if mask_ll.any():
        out.loc[mask_ll, "distance_km"] = haversine_km(
            station_lat,
            station_lon,
            out.loc[mask_ll, "lat"].to_numpy(),
            out.loc[mask_ll, "lon"].to_numpy(),
        )
    else:
        out["distance_km"] = pd.Series(dtype=float)

    return out



@dataclass(frozen=True)
class AnalysisContext:
    applied_filters: Dict[str, Any]
    filters_hash: str
    df_packets: pd.DataFrame
    metrics: Dict[str, Optional[float]]
    df_grid: Optional[pd.DataFrame] = None


def _filters_hash(filters: Dict[str, Any]) -> str:
    payload = json.dumps(filters, sort_keys=True, default=str).encode('utf-8')
    return hashlib.md5(payload).hexdigest()


def build_context(filters: Dict[str, Any], query_log: Optional[List[Dict]] = None) -> AnalysisContext:
    df = _load_packets_window_raw(
        db_path=filters["db_path"],
        since_iso=filters["since_iso"],
        since_epoch=filters["since_epoch"],
        dst_types=filters["dst_types"],
        station_callsign=filters["station_callsign"],
        only_heard_by=filters["only_heard_by"],
        igate_filter=filters["igate_filter"],
        source_mode=filters["source_mode"],
        qas_filter=filters["qas_filter"],
        limit_rows=filters["limit_rows"],
        query_log=query_log,
    )

    df = compute_features(df, filters["station_lat"], filters["station_lon"])
    # alias for readability
    if "rx_db" in df.columns and "signal_db" not in df.columns:
        df["signal_db"] = df["rx_db"]

    metrics: Dict[str, Optional[float]] = {
        "rows_window": int(len(df)) if not df.empty else 0,
        "max_distance_km": None,
        "p95_distance_km": None,
    }

    if not df.empty and "distance_km" in df.columns and df["distance_km"].notna().any():
        metrics["max_distance_km"] = float(df["distance_km"].max())
        metrics["p95_distance_km"] = float(np.nanpercentile(df["distance_km"].to_numpy(), 95))

    return AnalysisContext(
        applied_filters=filters,
        filters_hash=_filters_hash(filters),
        df_packets=df,
        metrics=metrics,
    )

# ---------------------------
# UI
# ---------------------------
default_filters = {
    "mode": "Standard",
    "db_path": DB_DEFAULT,
    "station_callsign": CALLSIGN_DEFAULT,
    "station_lat": float(ROOF_LAT_DEFAULT),
    "station_lon": float(ROOF_LON_DEFAULT),
    "hours": 6,
    "source_mode": "Heard-by station",
    "dst_types": ["OGNFNT", "OGFLR", "OGFLR7", "OGNSDR", "OGNDVS"],
    "only_local_radio": False,
    "igate_filter": "",
    "only_heard_by": True,
    "qas_filter": "",
    "basemap_label": DEFAULT_BASEMAP,
    "show_rings": True,
    "rings_km": [10, 25, 50, 100],
    "use_cov_grid": True,
    "point_size": 3,
    "limit_rows": 25000,
    "perf_cache": True,
    "map_max_points": 2000,
    "scatter_max_points": 1000,
    "debug_sql": False,
    "do_autorefresh": False,
    "show_cluster": False,
    "raw_packets_mode": False,
    "since_iso": (now_utc() - dt.timedelta(hours=6)).isoformat().replace("+00:00", "+00:00"),
    "since_epoch": int((now_utc() - dt.timedelta(hours=6)).timestamp()),
}

has_rf_prev = st.session_state.get("has_rf", True)
filters_apply = render_sidebar_filters(default_filters, now_utc, has_rf=has_rf_prev)

mode = filters_apply["mode"]
db_path = filters_apply["db_path"]
station_callsign = filters_apply["station_callsign"]
st.session_state["station_callsign"] = station_callsign
station_lat = filters_apply["station_lat"]
station_lon = filters_apply["station_lon"]
rf_receptions_available = table_exists_db(db_path, "rf_receptions")
hours = max(1, int(filters_apply["hours"]))

latest_ts_epoch = db_max_ts_epoch(db_path)
if latest_ts_epoch is not None:
    cutoff_epoch = int(latest_ts_epoch - hours * 3600)
    filters_apply["since_epoch"] = cutoff_epoch
    filters_apply["since_iso"] = dt.datetime.fromtimestamp(cutoff_epoch, tz=dt.timezone.utc).isoformat()
    st.session_state["filters_apply"]["since_epoch"] = cutoff_epoch
    st.session_state["filters_apply"]["since_iso"] = filters_apply["since_iso"]
source_mode = filters_apply["source_mode"]
dst_types = filters_apply["dst_types"]
igate_filter = filters_apply["igate_filter"]
only_heard_by = filters_apply["only_heard_by"]
qas_filter = filters_apply["qas_filter"]
basemap_label = filters_apply["basemap_label"]
show_rings = filters_apply["show_rings"]
show_cluster = filters_apply.get("show_cluster", False)
use_cov_grid = filters_apply.get("use_cov_grid", False)
rings_km = filters_apply["rings_km"]
point_size = filters_apply["point_size"]
limit_rows = filters_apply["limit_rows"]
perf_cache = filters_apply["perf_cache"]
map_max_points = filters_apply["map_max_points"]
scatter_max_points = filters_apply["scatter_max_points"]
debug_sql = filters_apply["debug_sql"]
do_autorefresh = filters_apply["do_autorefresh"]

if do_autorefresh:
    st.caption("Auto-refresh active (30s)")
    _set_query_ts(str(int(dt.datetime.now().timestamp())))
    _autorefresh(interval_ms=30000, key="autorefresh_30s")

query_log: List[Dict] = []
if debug_sql:
    _, last_ts = _db_meta_raw(db_path, query_log=query_log)
else:
    _, last_ts = db_meta(db_path)

header_container = st.container()
status_container = st.container()
kpi_container = st.container()
navigation_container = st.container()
content_container = st.container()

with header_container:
    st.header("OGN RF Coverage Analyzer")
    st.caption(f"Station {station_callsign}")
    st.markdown(f"DB: `{db_path}`")

# Precompute coverage probability KPIs (fast on grid)
grid_df_kpi = pd.DataFrame()
try:
    grid_df_kpi = pd.DataFrame()
except Exception:
    grid_df_kpi = pd.DataFrame()
packets_received = None
max_distance_grid = None
if not grid_df_kpi.empty:
    packets_received = int(np.nansum(pd.to_numeric(grid_df_kpi.get("packet_count"), errors="coerce")))
    max_distance_grid = float(pd.to_numeric(grid_df_kpi.get("max_distance_km"), errors="coerce").max())


# DB status logic (green/yellow/red)
db_error = False
db_reachable = os.path.exists(db_path)
if not db_reachable:
    db_error = True

if db_reachable:
    try:
        rf_issues = rf_sanity_check(db_path)
    except Exception:
        rf_issues = ["Database connection failed."]
else:
    rf_issues = ["Database not found."]
rows_in_window = 0
if db_reachable and not grid_df_kpi.empty and "packet_count" in grid_df_kpi.columns:
    rows_in_window = int(np.nansum(pd.to_numeric(grid_df_kpi.get("packet_count"), errors="coerce")))
if db_error:
    db_status_label = "DB status: ERROR (database unavailable)"
elif rows_in_window == 0:
    db_status_label = "DB status: OK (no packets in selected window)"
else:
    db_status_label = "DB status: OK"

# Grid status logic
grid_df_status = pd.DataFrame()
st.session_state["grid_df"] = grid_df_status if grid_df_status is not None else None
grid_cells = int(len(grid_df_status)) if grid_df_status is not None else 0
grid_enabled = bool(use_cov_grid)
if grid_df_status is not None and not grid_df_status.empty and grid_enabled:
    grid_status_label = "GRID READY"
else:
    grid_status_label = "GRID OFF — coverage grid not built"

last_packet_label = (last_ts[:19] + " UTC") if last_ts else "—"

packets_window = _load_packets_window_raw(
    db_path=db_path,
    since_iso=filters_apply["since_iso"],
    since_epoch=filters_apply["since_epoch"],
    dst_types=dst_types,
    station_callsign=station_callsign,
    only_heard_by=False,
    igate_filter="",
    source_mode="Heard-by station",
    qas_filter="",
    limit_rows=limit_rows,
    )
test_igate = str(filters_apply.get("test_igate", "")).strip()
test_fanet_igate = str(filters_apply.get("test_fanet_igate", "")).strip()
station_cs_effective = str(test_igate or station_callsign).upper()

receptions_window = _load_rf_receptions_window_raw(
    db_path=db_path,
    since_epoch=filters_apply["since_epoch"],
    limit_rows=limit_rows,
    station_id=station_cs_effective,
)

if "qas" in packets_window.columns:
    qas_upper = packets_window["qas"].astype(str).str.upper()
    rf_packets_global = packets_window[qas_upper.isin(["QAR", "QAO"])].copy()
    internet_packets = packets_window[qas_upper.isin(["QAC", "QAX"])].copy()
    server_packets = packets_window[qas_upper.isin(["QAS"])].copy()
else:
    rf_packets_global = packets_window.iloc[0:0].copy()
    internet_packets = packets_window.iloc[0:0].copy()
    server_packets = packets_window.iloc[0:0].copy()

aircraft_packets = packets_window.dropna(subset=["lat", "lon"]).copy() if "lat" in packets_window.columns and "lon" in packets_window.columns else packets_window.iloc[0:0].copy()
network_packets = packets_window

if "dst" in packets_window.columns:
    dst_upper = packets_window["dst"].astype(str).str.upper()
    fanet_packets_global = packets_window[dst_upper == "OGNFNT"].copy()
else:
    fanet_packets_global = packets_window.iloc[0:0].copy()

rf_receiver_only_raw = pd.DataFrame()

data_source_mode = filters_apply.get("data_source", "APRS-IS gated")
dataset_mode = "STRICT_RF"
if not rf_receptions_available:
    data_source_mode = "APRS-IS gated coverage"
    dataset_mode = "STATION_RF"
elif data_source_mode == "Receiver-only RF":
    dataset_mode = "STATION_RF"
elif data_source_mode == "FANET local":
    dataset_mode = "STATION_RF"
elif data_source_mode == "OGN live tracking":
    dataset_mode = "NETWORK"
engine = RFAnalysisEngine(receptions_window, station_lat, station_lon)
dataset = engine.build_analysis_dataset(dataset_mode=dataset_mode, station_id=station_cs_effective)
station_analysis = engine.run_station_analysis(dataset_mode=dataset_mode, station_id=station_cs_effective)
network_analysis = engine.run_network_analysis(dataset_mode=dataset_mode, station_id=station_cs_effective)
rf_diagnostics = engine.run_rf_diagnostics(dataset_mode=dataset_mode, station_id=station_cs_effective)
# Sync grid status with dataset coverage grid
grid_df_status = dataset.get("coverage_grid")
if grid_df_status is None:
    grid_df_status = pd.DataFrame()
st.session_state["grid_df"] = grid_df_status
grid_cells = int(len(grid_df_status)) if grid_df_status is not None else 0
grid_status_label = ("GRID READY" if grid_enabled and not grid_df_status.empty else "GRID OFF — coverage grid not built")
if not grid_df_status.empty and "packet_count" in grid_df_status.columns:
    packets_received = int(np.nansum(pd.to_numeric(grid_df_status.get("packet_count"), errors="coerce")))
if not grid_df_status.empty and "max_distance_km" in grid_df_status.columns:
    max_distance_grid = float(pd.to_numeric(grid_df_status.get("max_distance_km"), errors="coerce").max())
st.write("packets_window:", len(packets_window)) 
st.write("rf_packets:", len(dataset.get("packets_rf", []))) 
st.write("coverage_grid:", len(dataset.get("coverage_grid", [])))
rf_packets = dataset.get("rf_receptions")
if rf_packets is None:
    rf_packets = pd.DataFrame()
if rf_packets.empty:
    st.warning(
        "No RF packets detected for this station in the selected time window."
    )
    # st.stop()
polar_coverage = []
rf_grid = first_valid_df(dataset.get("coverage_grid"))
rf_packets_global = first_valid_df(dataset.get("packets_rf"))
rf_gated_packets = rf_packets
rf_gated_grid = rf_grid
fanet_local = pd.DataFrame()
fanet_grid = pd.DataFrame()
rf_receiver_only_packets = pd.DataFrame()
rf_receiver_only_grid = pd.DataFrame()
azimuth_stats = None
azimuth_footprint = None
rf_global_count = int(len(rf_packets_global))
rf_count = int(len(rf_packets))
internet_count = int(len(internet_packets))
server_count = int(len(server_packets))
has_rf = rf_count > 0
st.session_state["has_rf"] = has_rf
rf_packets_heard = (
    int(rf_gated_packets["igate"].astype(str).str.upper().eq(station_cs_effective).sum())
    if rf_gated_packets is not None and "igate" in rf_gated_packets.columns and station_cs_effective
    else None
)
rf_local = rf_gated_packets
rf_local_count = int(len(rf_local))
rf_local_aircraft = int(rf_local["src"].nunique()) if "src" in rf_local.columns else 0
rf_global_aircraft = int(rf_packets_global["src"].nunique()) if rf_packets_global is not None and "src" in rf_packets_global.columns else 0
rf_receiver_only_count = int(len(rf_receiver_only_packets))
rf_receiver_only_aircraft = int(rf_receiver_only_packets["src"].nunique()) if "src" in rf_receiver_only_packets.columns else 0

station_matrix = None
overlap = dataset.get("station_overlap_matrix")
redundancy = None

# Dataset status (RF + FANET) for clarity when sample sizes are low
rf_recommended = 2000
fanet_packets = int(len(fanet_local)) if fanet_local is not None else 0
fanet_devices = int(fanet_local["src"].nunique()) if fanet_local is not None and "src" in fanet_local.columns else 0
rf_quality = "LOW" if rf_local_count < 200 else "MEDIUM" if rf_local_count < rf_recommended else "GOOD"
fanet_quality = "LOW" if fanet_packets < 50 else "MEDIUM" if fanet_packets < 300 else "GOOD"
rf_badge = "🔴 LOW" if rf_quality == "LOW" else "🟡 MEDIUM" if rf_quality == "MEDIUM" else "🟢 GOOD"
fanet_badge = "🔴 LOW" if fanet_quality == "LOW" else "🟡 MEDIUM" if fanet_quality == "MEDIUM" else "🟢 GOOD"
rf_last_24h = None
rf_last_7d = None
if "ts_epoch" in rf_local.columns and not rf_local.empty:
    ts = pd.to_numeric(rf_local["ts_epoch"], errors="coerce")
    latest = ts.max()
    if pd.notna(latest):
        rf_last_24h = int((ts >= (latest - 24 * 3600)).sum())
        rf_last_7d = int((ts >= (latest - 7 * 24 * 3600)).sum())
with st.container():
    st.markdown("### Dataset status")
    st.markdown("**RF dataset**")
    st.write(
        f"RF packets (local): {fmt_int(rf_local_count)}  \n"
        f"RF packets last 24h: {fmt_int(rf_last_24h) if rf_last_24h is not None else '—'}  \n"
        f"RF packets last 7d: {fmt_int(rf_last_7d) if rf_last_7d is not None else '—'}  \n"
        f"Coverage readiness: **{rf_badge}**  \n"
        f"Recommended dataset: ≥ {fmt_int(rf_recommended)} packets"
    )
    st.markdown("**RF receiver-only (not gated)**")
    st.write(
        f"RF receiver-only packets: {fmt_int(rf_receiver_only_count)}  \n"
        f"RF receiver-only aircraft: {fmt_int(rf_receiver_only_aircraft)}  \n"
        "Badge: **Receiver-only (not gated)**"
    )
    st.markdown("**FANET dataset**")
    st.write(
        f"FANET packets (local): {fmt_int(fanet_packets)}  \n"
        f"FANET devices: {fmt_int(fanet_devices)}  \n"
        f"Network activity: **{fanet_badge}**"
    )
    if rf_local_count < 200:
        st.warning(
            f"DATASET TOO SMALL FOR RF COVERAGE ANALYSIS\n\n"
            f"RF packets heard by this station: {fmt_int(rf_local_count)}\n"
            f"Recommended RF dataset: ≥ {fmt_int(rf_recommended)} packets"
        )
    st.caption("RF dataset completeness")
    st.progress(min(rf_local_count / rf_recommended, 1.0))
    if rf_receiver_only_count > 0 and rf_local_count == 0:
        st.warning(
            "This station receives RF but does not gate packets to APRS-IS.\n"
            "RF coverage analysis requires gated packets (qAR/qAO)."
        )
    st.caption(f"Analysis source: {data_source_mode}")
    if not rf_receptions_available:
        st.caption("Dataset: packets where igate = station")

with kpi_container:
    k1, k2, k3, k4, k5 = st.columns(DASHBOARD_COLUMNS)
    packets_total = int(len(rf_packets)) if rf_packets is not None else 0
    aircraft_total = int(rf_packets["src"].nunique()) if rf_packets is not None and "src" in rf_packets.columns else 0
    max_dist = float(rf_packets["distance_km"].max()) if rf_packets is not None and "distance_km" in rf_packets.columns else None
    p95_dist = (
        float(rf_packets["distance_km"].quantile(0.95))
        if rf_packets is not None and "distance_km" in rf_packets.columns and not rf_packets.empty
        else None
    )
    metric_card(k1, "RF packets", fmt_int(packets_total))
    metric_card(k2, "Aircraft", fmt_int(aircraft_total))
    metric_card(k3, "Max distance", f"{fmt_float(max_dist, 1)} km" if max_dist is not None else "—")
    metric_card(k4, "P95 distance", f"{fmt_float(p95_dist, 1)} km" if p95_dist is not None else "—")
    metric_card(k5, "Grid cells", fmt_int(len(rf_grid)) if rf_grid is not None else "—")
    k6, k7, k8, k9, k10 = st.columns(DASHBOARD_COLUMNS)
    metric_card(k6, "Internet packets", fmt_int(internet_count))
    metric_card(k7, "Server packets", fmt_int(server_count))
    metric_card(k8, "RF packets (this station)", fmt_int(rf_packets_heard) if rf_packets_heard is not None else "—")
    metric_card(k9, "RF global packets", fmt_int(rf_global_count))
    metric_card(k10, "RF local packets", fmt_int(rf_local_count))

with status_container:
    st.caption(
        f"{db_status_label} | {grid_status_label} | Last packet: {last_packet_label}"
    )

if rf_issues:
    for issue in rf_issues:
        st.warning(f"RF environment check: {issue}")
else:
    st.success("RF environment check passed")

apply_ts = st.session_state.get("last_apply_ts")
apply_time = apply_ts.strftime("%H:%M:%S") if apply_ts else "—"
types_str = "/".join(dst_types) if dst_types else "—"
st.caption(f"Active filters: Station={station_callsign} | Window={hours}h | Types={types_str} | Mode={mode} — Last apply: {apply_time}")

raw_packets_mode = bool(st.session_state.get("filters_apply", {}).get("raw_packets_mode", False))
st.sidebar.write("Dataset mode:", dataset.get("dataset_mode"))
st.sidebar.write("Coverage cells:", len(dataset.get("coverage_grid", [])))
st.sidebar.write("Stations detected:", len(dataset.get("stations", [])))

with navigation_container:
    page = st.sidebar.radio(
        "Navigation",
        [
            "Station Intelligence",
            "Overview",
            "Coverage Explorer",
            "Propagation",
            "Network",
            "Diagnostics",
            "Network Intelligence",
        ]
    )
with st.expander("Advanced settings", expanded=False):
    with st.form("advanced_settings_form"):
        st.subheader("Map settings")
        basemap_label_adv = st.selectbox(
            "Basemap",
            list(BASEMAPS.keys()),
            index=list(BASEMAPS.keys()).index(st.session_state["filters_edit"]["basemap_label"]),
        )
        point_size_adv = st.slider("Marker size", 1, 10, int(st.session_state["filters_edit"]["point_size"]))
        show_cluster_adv = st.checkbox(
            "Cluster markers (slower)",
            value=bool(st.session_state["filters_edit"].get("show_cluster", False)),
        )
        show_rings_adv = st.checkbox(
            "Show range rings",
            value=bool(st.session_state["filters_edit"].get("show_rings", True)),
        )
        rings_km_adv = st.multiselect(
            "Rings (km)",
            [5, 10, 25, 50, 75, 100, 150, 200],
            default=st.session_state["filters_edit"].get("rings_km", [10, 25, 50, 100]),
        )

        st.subheader("Performance")
        limit_rows_adv = st.slider(
            "Max grid cells",
            1000,
            50000,
            int(st.session_state["filters_edit"]["limit_rows"]),
            help="Maximum number of grid cells used for coverage computation",
        )
        map_max_points_adv = st.slider(
            "Max map points",
            100,
            5000,
            int(st.session_state["filters_edit"]["map_max_points"]),
            help="Maximum number of markers displayed on the map",
        )
        scatter_max_points_adv = st.slider(
            "Max scatter points",
            100,
            5000,
            int(st.session_state["filters_edit"]["scatter_max_points"]),
            help="Maximum number of points rendered in charts",
        )
        do_autorefresh_adv = st.checkbox(
            "Auto-refresh (30s)",
            value=bool(st.session_state["filters_edit"]["do_autorefresh"]),
        )
        perf_cache_adv = st.checkbox(
            "Enable cache",
            value=bool(st.session_state["filters_edit"].get("perf_cache", True)),
        )

        st.subheader("Developer")
        mode_adv = st.selectbox(
            "Interface mode",
            ["Standard", "Advanced", "Expert"],
            index=["Standard", "Advanced", "Expert"].index(st.session_state["filters_edit"]["mode"]),
        )
        test_igate_adv = st.text_input(
            "Test IGate (optional)",
            st.session_state["filters_edit"].get("test_igate", ""),
            help="Override IGate callsign used for local RF checks (debug/validation).",
        )
        test_fanet_igate_adv = st.text_input(
            "Test FANET IGate (optional)",
            st.session_state["filters_edit"].get("test_fanet_igate", ""),
            help="Override IGate callsign used for FANET local checks (debug/validation).",
        )
        debug_sql_adv = st.checkbox(
            "Debug SQL timings",
            value=bool(st.session_state["filters_edit"]["debug_sql"]),
        )
        raw_packets_mode_adv = st.checkbox(
            "Raw packets mode (Debug only)",
            value=bool(st.session_state["filters_edit"].get("raw_packets_mode", False)),
        )

        apply_adv = st.form_submit_button("Apply advanced settings")

    if apply_adv:
        st.session_state["filters_edit"] = {
            **st.session_state["filters_edit"],
            "basemap_label": basemap_label_adv,
            "point_size": int(point_size_adv),
            "show_cluster": bool(show_cluster_adv),
            "show_rings": bool(show_rings_adv),
            "rings_km": list(rings_km_adv),
            "limit_rows": int(limit_rows_adv),
            "map_max_points": int(map_max_points_adv),
            "scatter_max_points": int(scatter_max_points_adv),
            "do_autorefresh": bool(do_autorefresh_adv),
            "perf_cache": bool(perf_cache_adv),
            "mode": mode_adv,
            "test_igate": test_igate_adv.strip(),
            "test_fanet_igate": test_fanet_igate_adv.strip(),
            "debug_sql": bool(debug_sql_adv),
            "raw_packets_mode": bool(raw_packets_mode_adv),
        }
        st.session_state["filters_apply"] = {
            **st.session_state["filters_apply"],
            "basemap_label": basemap_label_adv,
            "point_size": int(point_size_adv),
            "show_cluster": bool(show_cluster_adv),
            "show_rings": bool(show_rings_adv),
            "rings_km": list(rings_km_adv),
            "limit_rows": int(limit_rows_adv),
            "map_max_points": int(map_max_points_adv),
            "scatter_max_points": int(scatter_max_points_adv),
            "do_autorefresh": bool(do_autorefresh_adv),
            "perf_cache": bool(perf_cache_adv),
            "mode": mode_adv,
            "test_igate": test_igate_adv.strip(),
            "test_fanet_igate": test_fanet_igate_adv.strip(),
            "debug_sql": bool(debug_sql_adv),
            "raw_packets_mode": bool(raw_packets_mode_adv),
        }
        if mode_adv == "Expert":
            st.info("Expert mode enabled.")
        else:
            st.info("Advanced settings applied.")

    if st.session_state["filters_apply"]["mode"] == "Expert":
        st.subheader("DB maintenance")
        safe_opt = st.button("ANALYZE / OPTIMIZE")
        vacuum_opt = st.button("VACUUM")
        create_idx = st.button("Create indexes")
        if safe_opt:
            with st.spinner("Optimizing..."):
                try:
                    optimize_db(st.session_state["filters_apply"]["db_path"], vacuum=False)
                    st.success("Optimization completed.")
                except Exception as e:
                    st.error(f"Optimization failed: {e!r}")
        if vacuum_opt:
            with st.spinner("VACUUM in progress..."):
                try:
                    optimize_db(st.session_state["filters_apply"]["db_path"], vacuum=True)
                    st.success("VACUUM completed.")
                except Exception as e:
                    st.error(f"VACUUM failed: {e!r}")
        if create_idx:
            with st.spinner("Creating indexes..."):
                try:
                    create_indexes(st.session_state["filters_apply"]["db_path"])
                    st.success("Indexes created.")
                except Exception as e:
                    st.error(f"Index creation failed: {e!r}")




def get_packets_context() -> AnalysisContext:
    ctx_key = _filters_hash({**filters_apply, "_ctx": "packets"})
    cached_ctx = st.session_state.get("packets_ctx")
    cached_hash = st.session_state.get("packets_ctx_hash")
    if cached_ctx is not None and cached_hash == ctx_key:
        return cached_ctx
    with st.status("Loading packets", expanded=False) as status:
        ctx = build_context(filters_apply, query_log=query_log if debug_sql else None)
        status.update(label="Packets loaded", state="complete")
    grid_df_ctx = st.session_state.get("grid_df")
    if grid_df_ctx is not None:
        ctx = replace(ctx, df_grid=grid_df_ctx)
    st.session_state["packets_ctx"] = ctx
    st.session_state["packets_ctx_hash"] = ctx_key
    return ctx


ui_ctx = {
    "db_path": db_path,
    "filters_apply": filters_apply,
    "station_callsign": station_callsign,
    "station_lat": station_lat,
    "station_lon": station_lon,
    "data_source": filters_apply.get("data_source", "APRS-IS gated"),
    "test_fanet_igate": filters_apply.get("test_fanet_igate", ""),
    "BASEMAPS": BASEMAPS,
    "basemap_label": basemap_label,
    "max_distance_grid": max_distance_grid,
    "use_cov_grid": use_cov_grid,
    "map_max_points": map_max_points,
    "point_size": point_size,
    "show_cluster": show_cluster,
    "show_rings": show_rings,
    "rings_km": rings_km,
    "dst_types": dst_types,
    "limit_rows": limit_rows,
    "hours": hours,
    "raw_packets_mode": raw_packets_mode,
    "dataset": dataset,
    "station_analysis": station_analysis,
    "network_analysis": network_analysis,
    "rf_diagnostics": rf_diagnostics,
    "grid_df_kpi": grid_df_kpi,
    "rf_packets": rf_packets,
    "rf_packets_global": rf_packets_global,
    "rf_gated_packets": rf_gated_packets,
    "rf_local": rf_local,
    "rf_receiver_only_raw": rf_receiver_only_raw,
    "rf_receiver_only_packets": rf_receiver_only_packets,
    "fanet_packets_global": fanet_packets_global,
    "fanet_local": fanet_local,
    "rf_grid": rf_grid,
    "packets_window": packets_window,
    "rf_packets": rf_packets,
    "aircraft_packets": aircraft_packets,
    "network_packets": network_packets,
    "internet_packets": internet_packets,
    "server_packets": server_packets,
    "rf_count": rf_count,
    "rf_global_count": rf_global_count,
    "rf_receiver_only_count": rf_receiver_only_count,
    "rf_receiver_only_aircraft": rf_receiver_only_aircraft,
    "rf_local_count": rf_local_count,
    "rf_local_aircraft": rf_local_aircraft,
    "rf_global_aircraft": rf_global_aircraft,
    "internet_count": internet_count,
    "server_count": server_count,
    "has_rf": has_rf,
    "station_matrix": station_matrix,
    "station_overlap": overlap,
    "redundancy": redundancy,
    "azimuth_stats": azimuth_stats,
    "azimuth_footprint": azimuth_footprint,
    "polar_coverage": polar_coverage,
    "pd": pd,
    "np": np,
    "os": os,
    "_load_packets_window_raw": _load_packets_window_raw,
    "get_packets_context": get_packets_context,
    "parse_compare_stations": _parse_compare_stations,
    "fmt_int": fmt_int,
    "fmt_float": fmt_float,
}

left_panel, center_panel, right_panel = st.columns([1, 3, 1], gap="large")

with left_panel:
    st.subheader("Navigation")
    page = st.radio(
        "View",
        [
            "Station Intelligence",
            "Overview",
            "Coverage Explorer",
            "Propagation",
            "Network",
            "Diagnostics",
            "Network Intelligence",
        ],
        key="main_nav_page",
        label_visibility="collapsed",
    )

with center_panel:
    if page == "Station Intelligence":
        render_station_intelligence_tab(ui_ctx)

    elif page == "Overview":
        render_overview_tab(ui_ctx)

    elif page == "Coverage Explorer":
        render_coverage_explorer_tab(ui_ctx)

    elif page == "Propagation":
        render_signal_tab(ui_ctx)

    elif page == "Network":
        render_network_tab(ui_ctx)

    elif page == "Diagnostics":
        render_diagnostics_tab(ui_ctx)

    elif page == "Network Intelligence":
        render_network_intelligence_tab(ui_ctx)

with right_panel:
    st.subheader("Inspector")
    st.info("Object inspector placeholder")
    st.caption(f"View: {page}")


if _PROFILER:
    _PROFILER.disable()
    st.caption("Profiling enabled (results printed to console).")
    _s = io.StringIO()
    _stats = pstats.Stats(_PROFILER, stream=_s)
    _stats.sort_stats("cumtime")
    _stats.print_stats(30)
    print(_s.getvalue())

# Footer
with st.container():
    st.divider()
    grid_df = rf_grid if isinstance(rf_grid, pd.DataFrame) else pd.DataFrame()
    st.caption(
        f"Packets processed: {fmt_int(packets_received) if packets_received is not None else '—'} • "
        f"Grid cells: {fmt_int(len(grid_df)) if not grid_df.empty else '—'} • "
        f"Last update: {(last_ts[:19] + 'Z') if last_ts else '—'}"
    )










