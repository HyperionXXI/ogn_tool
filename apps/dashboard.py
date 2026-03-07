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
import sqlite3
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

from ogn_tool.config import get_config
from ogn_tool.db import connect
from ogn_tool.rf_analysis import compute_azimuth_stats, compute_distance_probability, reliable_distance_km
from ogn_tool.analysis import polar as analysis_polar
from ogn_tool.analysis import signal_distance as analysis_signal_distance
from ogn_tool.analysis import altitude_distance as analysis_altitude_distance
from ogn_tool.analysis import shadow_map as analysis_shadow_map
from ogn_tool.analysis import station_range as analysis_station_range
from ogn_tool.analysis import terrain as analysis_terrain
from ogn_tool.analysis import station_compare as analysis_station_compare
from ogn_tool.analysis import station_quality as analysis_station_quality
from ogn_tool.analysis import antenna_health as analysis_antenna_health
from ogn_tool.analysis import radio_horizon as analysis_radio_horizon
from ogn_tool.analysis.grid_loader import load_coverage_grid as load_coverage_grid_base

try:
    from streamlit_folium import st_folium
    import folium
    from folium.features import DivIcon
    from folium.plugins import HeatMap, MarkerCluster
except Exception as e:  # pragma: no cover
    st.error("Missing dependency: streamlit-folium / folium. Install: pip install streamlit-folium folium")
    raise

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
    page_title="OGN / APRS-IS — Dashboard local",
    layout="wide",
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

DB_STALE_WARN_S = 90  # warning if last packet older than that
DB_STALE_ERR_S = 900  # "frozen" if last packet older than that

RE_DB = re.compile(r"(?P<db>\d+(?:\.\d+)?)\s*dB\b")
RE_COORD = re.compile(r"(?P<lat>\d{2})(?P<latm>\d{2}\.\d{2})(?P<NS>[NS])[/\\](?P<lon>\d{3})(?P<lonm>\d{2}\.\d{2})(?P<EW>[EW])")


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
    return f"{x:.{nd}f}"


def now_utc() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def iso_utc(dtobj: dt.datetime) -> str:
    if dtobj.tzinfo is None:
        dtobj = dtobj.replace(tzinfo=dt.timezone.utc)
    return dtobj.isoformat().replace("+00:00", "Z")


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
    """Return (rows_total, max_ts_utc) from packets table, robust."""
    if not os.path.exists(db_path):
        return 0, None
    con = sqlite3.connect(db_path)
    try:
        sql = "SELECT COUNT(*) AS cnt, MAX(ts_utc) AS max_ts FROM packets"
        t0 = time.perf_counter()
        row = con.execute(sql).fetchone()
        dt_ms = (time.perf_counter() - t0) * 1000.0
        if query_log is not None:
            query_log.append({"query": "db_meta", "ms": round(dt_ms, 2), "rows": 1})
        return int(row[0]), row[1]
    finally:
        con.close()


@st.cache_data(ttl=30, show_spinner=False)
def db_meta(db_path: str) -> Tuple[int, Optional[str]]:
    return _db_meta_raw(db_path)

def optimize_db(db_path: str, vacuum: bool = False) -> None:
    con = sqlite3.connect(db_path, timeout=30)
    try:
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
        con.execute("ANALYZE;")
        con.execute("PRAGMA optimize;")
        if vacuum:
            con.execute("VACUUM;")
        con.commit()
    finally:
        con.close()

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
    con = sqlite3.connect(db_path, timeout=30)
    try:
        con.execute("PRAGMA journal_mode=WAL;")
        con.execute("PRAGMA synchronous=NORMAL;")
        con.execute("CREATE INDEX IF NOT EXISTS idx_packets_epoch ON packets(ts_epoch DESC);")
        con.execute("CREATE INDEX IF NOT EXISTS idx_packets_epoch_dst ON packets(ts_epoch DESC, dst);")
        con.execute("CREATE INDEX IF NOT EXISTS idx_packets_epoch_dst_igate_qas ON packets(ts_epoch DESC, dst, igate, qas);")
        con.execute("CREATE INDEX IF NOT EXISTS idx_packets_qas_epoch ON packets(qas, ts_epoch DESC);")
        con.execute("CREATE INDEX IF NOT EXISTS idx_packets_igate_epoch ON packets(igate, ts_epoch DESC);")
        tables = {row[0] for row in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if "coverage_grid" in tables:
            con.execute("CREATE INDEX IF NOT EXISTS idx_covgrid_ts ON coverage_grid(last_ts_epoch DESC);")
            con.execute("CREATE INDEX IF NOT EXISTS idx_covgrid_xy ON coverage_grid(cell_x, cell_y);")
        con.commit()
    finally:
        con.close()

def _build_where(
    since_iso: str,
    since_epoch: int,
    use_epoch: bool,
    dst_types: List[str],
    station_callsign: str,
    only_heard_by: bool,
    igate_filter: str,
    source_mode: str,
    qas_filter: str,
) -> Tuple[str, List]:
    if use_epoch:
        where = ["ts_epoch >= ?"]
        params: List = [int(since_epoch)]
    else:
        ts_norm = "(CASE WHEN substr(ts_utc,-1)='Z' THEN substr(ts_utc,1,length(ts_utc)-1)||'+00:00' ELSE ts_utc END)"
        where = [f"{ts_norm} >= ?"]
        params = [since_iso]

    if dst_types:
        where.append("dst IN ({})".format(",".join(["?"] * len(dst_types))))
        params.extend(dst_types)

    if igate_filter.strip():
        where.append("igate = ?")
        params.append(igate_filter.strip())

    if source_mode == "Heard-by station":
        if only_heard_by:
            where.append("(igate = ? OR raw LIKE ?)")
            params.append(station_callsign)
            params.append(f"%,{station_callsign}:%")
    else:
        # Radio station view: filter by qas token and igate signature
        qas_filter = qas_filter.strip()
        if qas_filter:
            if "*" in qas_filter:
                where.append("qas LIKE ?")
                params.append(qas_filter.replace("*", "%"))
            else:
                where.append("qas = ?")
                params.append(qas_filter)

    return " AND ".join(where), params


@st.cache_data(ttl=5, show_spinner=False)
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

    con = sqlite3.connect(db_path)
    try:
        cols = {row[1] for row in con.execute("PRAGMA table_info(packets)")}
        use_epoch = "ts_epoch" in cols

        where_sql, params = _build_where(
            since_iso=since_iso,
            since_epoch=since_epoch,
            use_epoch=use_epoch,
            dst_types=dst_types,
            station_callsign=station_callsign,
            only_heard_by=only_heard_by,
            igate_filter=igate_filter,
            source_mode=source_mode,
            qas_filter=qas_filter,
        )

        select_cols = "ts_epoch, ts_utc, src, dst, igate, qas, lat, lon, raw"
        order_col = "ts_epoch" if use_epoch else "ts_utc"
        sql = f"""
        SELECT
            {select_cols}
        FROM packets
        WHERE {where_sql}
        ORDER BY {order_col} DESC
        LIMIT ?
        """
        params2 = params + [int(limit_rows)]
        t0 = time.perf_counter()
        df = pd.read_sql_query(sql, con, params=params2)
        dt_ms = (time.perf_counter() - t0) * 1000.0
        if query_log is not None:
            query_log.append({"query": "load_packets_window", "ms": round(dt_ms, 2), "rows": int(len(df))})
    finally:
        con.close()

    return df


@st.cache_data(ttl=30, show_spinner=False)
def load_packets_window(
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
) -> pd.DataFrame:
    return _load_packets_window_raw(
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
    )


@st.cache_data(ttl=60, show_spinner=False)
def load_coverage_grid(db_path: str, since_epoch: int) -> pd.DataFrame:
    if not os.path.exists(db_path):
        return pd.DataFrame()
    con = sqlite3.connect(db_path)
    try:
        cols = {row[1] for row in con.execute("PRAGMA table_info(coverage_grid)")}
        if not cols:
            return pd.DataFrame()
        sql = """
        SELECT
            cell_x, cell_y, lat, lon, max_distance_km, best_rssi_db, packet_count, last_ts_epoch
        FROM coverage_grid
        WHERE last_ts_epoch >= ?
        ORDER BY last_ts_epoch DESC
        """
        return pd.read_sql_query(sql, con, params=(int(since_epoch),))
    except sqlite3.OperationalError:
        return pd.DataFrame()
    finally:
        con.close()


@st.cache_data(ttl=60, show_spinner=False)
def coverage_grid_exists(db_path: str) -> bool:
    if not os.path.exists(db_path):
        return False
    con = sqlite3.connect(db_path)
    try:
        row = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='coverage_grid'"
        ).fetchone()
        return row is not None
    finally:
        con.close()


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

if "filters_apply" not in st.session_state:
    st.session_state["filters_apply"] = default_filters.copy()
if "filters_edit" not in st.session_state:
    st.session_state["filters_edit"] = st.session_state["filters_apply"].copy()
if "last_apply_ts" not in st.session_state:
    st.session_state["last_apply_ts"] = now_utc()

with st.sidebar:
    with st.form("filters_form"):
        st.markdown("## Station")
        station_callsign = st.text_input("Callsign", st.session_state["filters_edit"]["station_callsign"])
        db_path = st.text_input("DB path", st.session_state["filters_edit"]["db_path"])
        station_lat = st.number_input("Latitude", value=float(st.session_state["filters_edit"]["station_lat"]), format="%.6f")
        station_lon = st.number_input("Longitude", value=float(st.session_state["filters_edit"]["station_lon"]), format="%.6f")

        st.markdown("## Time window")
        hours = st.slider("Time window (hours)", 1, 72, int(st.session_state["filters_edit"]["hours"]))

        st.markdown("## Data filters")
        source_mode = st.selectbox(
            "Packet source",
            ["Heard-by station", "Radio station view"],
            index=["Heard-by station", "Radio station view"].index(st.session_state["filters_edit"]["source_mode"]),
        )
        dst_types = st.multiselect(
            "Aircraft types",
            ["OGNFNT", "OGFLR", "OGFLR7", "OGNSDR", "OGNDVS"],
            default=st.session_state["filters_edit"]["dst_types"],
        )
        only_heard_by = st.checkbox("Coverage heard-by", value=bool(st.session_state["filters_edit"]["only_heard_by"]))
        only_local_radio = st.checkbox("Local radio only", value=bool(st.session_state["filters_edit"]["only_local_radio"]))
        igate_filter = st.text_input("IGate filter (optional)", value=st.session_state["filters_edit"]["igate_filter"])
        use_cov_grid = st.checkbox("Use coverage grid (recommended)", value=bool(st.session_state["filters_edit"].get("use_cov_grid", True)))

        st.caption("Filters are applied only when clicking 'Apply filters'.")
        apply_button = st.form_submit_button("Apply filters")

    if apply_button:
        st.session_state["filters_edit"] = {
            **st.session_state["filters_edit"],
            "db_path": db_path,
            "station_callsign": station_callsign,
            "station_lat": float(station_lat),
            "station_lon": float(station_lon),
            "hours": int(hours),
            "source_mode": source_mode,
            "dst_types": list(dst_types),
            "only_local_radio": bool(only_local_radio),
            "only_heard_by": bool(only_heard_by),
            "igate_filter": igate_filter,
            "use_cov_grid": bool(use_cov_grid),
        }

        applied = st.session_state["filters_edit"].copy()
        if applied["only_local_radio"]:
            applied["source_mode"] = "Radio station view"
            if not applied.get("igate_filter"):
                applied["igate_filter"] = applied["station_callsign"]
            applied["qas_filter"] = "qA*"
        else:
            applied["qas_filter"] = ""
        since_dt = now_utc() - dt.timedelta(hours=int(applied["hours"]))
        applied["since_iso"] = since_dt.isoformat().replace("+00:00", "+00:00")
        applied["since_epoch"] = int(since_dt.timestamp())
        st.session_state["filters_apply"] = applied
        st.session_state["last_apply_ts"] = now_utc()

filters_apply = st.session_state["filters_apply"]
if filters_apply["do_autorefresh"]:
    filters_apply = filters_apply.copy()
    since_dt = now_utc() - dt.timedelta(hours=int(filters_apply["hours"]))
    filters_apply["since_iso"] = since_dt.isoformat().replace("+00:00", "+00:00")
    filters_apply["since_epoch"] = int(since_dt.timestamp())

mode = filters_apply["mode"]
db_path = filters_apply["db_path"]
station_callsign = filters_apply["station_callsign"]
station_lat = filters_apply["station_lat"]
station_lon = filters_apply["station_lon"]
hours = max(1, int(filters_apply["hours"]))
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
btn_refresh = False
raw_packets_mode = filters_apply.get("raw_packets_mode", False)

if do_autorefresh:
    st.caption("Auto-refresh active (30s)")
    _set_query_ts(str(int(dt.datetime.now().timestamp())))
    _autorefresh(interval_ms=30000, key="autorefresh_30s")

query_log: List[Dict] = []
if debug_sql:
    rows_total, last_ts = _db_meta_raw(db_path, query_log=query_log)
else:
    rows_total, last_ts = db_meta(db_path)

header_container = st.container()
status_container = st.container()
kpi_container = st.container()
navigation_container = st.container()
content_container = st.container()

with header_container:
    st.header("OGN RF Coverage Analyzer")
    st.caption(f"Station {station_callsign}")
    st.markdown(f"DB: `{db_path}`")

# Freshness banner
fresh_state = "unknown"
age_s = None
if last_ts:
    try:
        last_dt = dt.datetime.fromisoformat(last_ts.replace("Z", "+00:00"))
        age_s = (now_utc() - last_dt).total_seconds()
        if age_s <= DB_STALE_WARN_S:
            fresh_state = "ok"
        elif age_s <= DB_STALE_ERR_S:
            fresh_state = "warn"
        else:
            fresh_state = "err"
    except Exception:
        fresh_state = "unknown"

# Precompute coverage probability KPIs (fast on grid)
grid_df_kpi = pd.DataFrame()
try:
    grid_df_kpi = load_coverage_grid(db_path, filters_apply["since_epoch"])
except Exception:
    grid_df_kpi = pd.DataFrame()
packets_received = None
max_distance_grid = None
d90 = None
if not grid_df_kpi.empty:
    packets_received = int(np.nansum(pd.to_numeric(grid_df_kpi.get("packet_count"), errors="coerce")))
    max_distance_grid = float(pd.to_numeric(grid_df_kpi.get("max_distance_km"), errors="coerce").max())
    dist_bins_kpi = pd.to_numeric(grid_df_kpi.get("max_distance_km", pd.Series(dtype=float)), errors="coerce").to_numpy()
    pkt_bins_kpi = pd.to_numeric(grid_df_kpi.get("packet_count", pd.Series(dtype=float)), errors="coerce").to_numpy()
    centers_kpi, probs_kpi = compute_distance_probability(dist_bins_kpi, pkt_bins_kpi, bin_size_km=5.0)
    if centers_kpi.size > 0:
        d90 = reliable_distance_km(centers_kpi, probs_kpi, threshold=0.9)

# DB status logic (green/yellow/red)
db_error = False
db_reachable = os.path.exists(db_path)
if not db_reachable:
    db_error = True
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
grid_df_status = load_coverage_grid_base(db_path)
st.session_state["grid_df"] = grid_df_status if grid_df_status is not None else None
grid_cells = int(len(grid_df_status)) if grid_df_status is not None else 0
grid_enabled = bool(use_cov_grid)
if grid_df_status is not None and grid_enabled:
    grid_status_label = "GRID READY"
else:
    grid_status_label = "GRID OFF — coverage grid not built"

last_packet_label = (last_ts[:19] + " UTC") if last_ts else "—"

with status_container:
    s1, s2, s3, s4, s5 = st.columns(5)
    with s1:
        st.metric("DB status", db_status_label)
    with s2:
        st.metric("Grid status", grid_status_label)
        if grid_df_status is None or not grid_enabled:
            st.caption("Run scripts/build_coverage_grid.py to enable coverage analysis")
    with s3:
        st.metric("Last packet", last_packet_label)
    with s4:
        st.metric("Packets in window", fmt_int(rows_in_window))
    with s5:
        st.metric("Grid cells", fmt_int(grid_cells) if grid_df_status is not None else "—")

apply_ts = st.session_state.get("last_apply_ts")
apply_time = apply_ts.strftime("%H:%M:%S") if apply_ts else "—"
types_str = "/".join(dst_types) if dst_types else "—"
st.info(f"Active filters: Station={station_callsign} | Window={hours}h | Types={types_str} | Mode={mode} — Last apply: {apply_time}")


with kpi_container:
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        packets_received_display = 0 if packets_received is None else packets_received
        st.metric("Packets in window", fmt_int(packets_received_display))
    with k2:
        st.metric("Last packet (UTC)", (last_ts[:19] + "Z") if last_ts else "—")
    with k3:
        st.metric("Reliable distance", f"{fmt_float(d90, 1)} km" if d90 is not None else "—")
    with k4:
        st.metric("Max distance", f"{fmt_float(max_distance_grid, 1)} km" if max_distance_grid is not None else "—")
    with k5:
        st.empty()

with navigation_container:
    view = st.segmented_control(
        "Analysis",
        [
            "Coverage",
            "Signal",
            "RF diagnostics",
            "Debug",
        ],
        default="Coverage",
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
        do_autorefresh_adv = st.checkbox("Auto-refresh (30s)", value=bool(st.session_state["filters_edit"]["do_autorefresh"]))
        perf_cache_adv = st.checkbox("Enable cache", value=bool(st.session_state["filters_edit"].get("perf_cache", True)))

        st.subheader("Developer")
        mode_adv = st.selectbox(
            "Interface mode",
            ["Standard", "Advanced", "Expert"],
            index=["Standard", "Advanced", "Expert"].index(st.session_state["filters_edit"]["mode"]),
        )
        debug_sql_adv = st.checkbox("Debug SQL timings", value=bool(st.session_state["filters_edit"]["debug_sql"]))
        raw_packets_mode_adv = st.checkbox("Raw packets mode (Debug only)", value=bool(st.session_state["filters_edit"].get("raw_packets_mode", False)))

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


def _color_from_value(val: float, vmin: float, vmax: float) -> str:
    if val is None or (isinstance(val, float) and math.isnan(val)):
        return "#999999"
    if vmax <= vmin:
        t = 0.5
    else:
        t = (val - vmin) / (vmax - vmin)
        t = max(0.0, min(1.0, t))
    if t < 0.25:
        return "#2563eb"
    if t < 0.5:
        return "#06b6d4"
    if t < 0.75:
        return "#22c55e"
    if t < 0.9:
        return "#eab308"
    return "#ef4444"


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


def render_coverage_view() -> None:
    section_map = st.container()
    section_rssi = st.container()
    section_distance = st.container()

    df_grid = load_coverage_grid(db_path, filters_apply["since_epoch"])

    with section_map:
        st.subheader("Coverage map")
        raw_packets = _load_packets_window_raw(
            db_path=db_path,
            since_iso=filters_apply["since_iso"],
            since_epoch=filters_apply["since_epoch"],
            dst_types=[],
            station_callsign=station_callsign,
            only_heard_by=False,
            igate_filter="",
            source_mode="Heard-by station",
            qas_filter="",
            limit_rows=limit_rows,
        )
        shadow_ctx = {
            "packets": raw_packets,
            "station_callsign": station_callsign,
            "cell_size_km": 3.0,
            "window_hours": hours,
        }
        result = analysis_shadow_map.analyze(shadow_ctx)
        if not result.get("implemented"):
            reason = (result.get("summary") or {}).get("reason")
            if reason == "no_local_packets_in_window":
                summary = result.get("summary") or {}
                msg = "No local packets found for this station in the selected time window."
                last_ts = summary.get("last_local_rx_ts")
                if last_ts:
                    msg = f"{msg} Last local reception: {last_ts}."
                st.info(msg)
            else:
                st.info("Coverage map not available.\nRequires coverage_grid dataset.")
        else:
            summary = result.get("summary") or {}
            data = result.get("data")
            st.markdown("**Radio shadow map**")
            if data is None or (hasattr(data, "empty") and data.empty) or (hasattr(data, "__len__") and len(data) == 0):
                st.info("No data available.")
            else:
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1:
                    st.metric("Cells", fmt_int(summary.get("cells_total")))
                with c2:
                    st.metric("Shadow cells", fmt_int(summary.get("shadow_cells")))
                with c3:
                    val = summary.get("coverage_mean")
                    st.metric("Coverage mean", f"{fmt_float(val, 2)}" if val is not None else "—")
                with c4:
                    st.empty()
                with c5:
                    st.empty()
                d1, d2, d3, d4, d5 = st.columns(5)
                with d1:
                    st.metric("Local points", fmt_int(summary.get("local_points")))
                with d2:
                    st.metric("Local igate", fmt_int(summary.get("local_points_igate")))
                with d3:
                    st.metric("Local raw", fmt_int(summary.get("local_points_raw")))
                with d4:
                    st.empty()
                with d5:
                    st.empty()
                st.dataframe(data.head(30), use_container_width=True)

    with section_rssi:
        st.subheader("RSSI heatmap")
        result = analysis_signal_distance.analyze(df_grid)
        if not result.get("implemented"):
            st.info("RSSI heatmap not available.\nRequires RSSI aggregation per grid cell.")

    with section_distance:
        st.subheader("Distance heatmap")
        result = analysis_station_range.analyze(df_grid)
        if not result.get("implemented"):
            st.info("Distance heatmap not available.\nRequires distance statistics.")
        else:
            summary = result.get("summary") or {}
            data = result.get("data")
            if data is None or (hasattr(data, "empty") and data.empty) or (hasattr(data, "__len__") and len(data) == 0):
                st.info("No data available.")
            if summary:
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1:
                    st.metric("Packet total", fmt_int(summary.get("packet_total")))
                with c2:
                    st.metric("Grid cells", fmt_int(summary.get("grid_cells")))
                with c3:
                    val = summary.get("max_distance_km")
                    st.metric("Max distance (km)", f"{fmt_float(val, 1)}" if val is not None else "—")
                with c4:
                    val = summary.get("p95_distance_km")
                    st.metric("P95 distance (km)", f"{fmt_float(val, 1)}" if val is not None else "—")
                with c5:
                    st.empty()
            else:
                st.info("No distance statistics available.")


def render_signal_view() -> None:
    section_signal = st.container()
    section_altitude = st.container()
    section_distribution = st.container()

    df_grid = load_coverage_grid(db_path, filters_apply["since_epoch"])
    packets_signal = _load_packets_window_raw(
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

    with section_signal:
        st.subheader("Signal vs distance (SNR dB)")
        result = analysis_signal_distance.analyze(
            packets_signal,
            station_lat=station_lat,
            station_lon=station_lon,
        )
        if not result.get("implemented"):
            st.info("Signal vs distance analysis not implemented.")
        else:
            summary = result.get("summary") or {}
            data = result.get("data")
            if data is None or (hasattr(data, "empty") and data.empty) or (hasattr(data, "__len__") and len(data) == 0):
                st.info("No data available.")
            else:
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1:
                    st.metric("Packet total", fmt_int(summary.get("packet_total")))
                with c2:
                    val = summary.get("max_distance_km")
                    st.metric("Max distance (km)", f"{fmt_float(val, 1)}" if val is not None else "—")
                with c3:
                    val = summary.get("mean_rssi")
                    st.metric("Mean signal (SNR dB)", f"{fmt_float(val, 1)}" if val is not None else "—")
                with c4:
                    val = summary.get("p95_distance_km")
                    st.metric("P95 distance (km)", f"{fmt_float(val, 1)}" if val is not None else "—")
                with c5:
                    st.empty()
                if "distance_km" in data.columns and "rssi_db" in data.columns:
                    st.markdown("**RSSI vs distance**")
                    binned = result.get("binned_data")
                    if go is not None:
                        fig = go.Figure()
                        fig.add_trace(
                            go.Scatter(
                                x=data["distance_km"],
                                y=data["rssi_db"],
                                mode="markers",
                                name="Packets",
                                marker=dict(size=2, opacity=0.18),
                            )
                        )
                        if binned is not None and not binned.empty:
                            fig.add_trace(
                                go.Scatter(
                                    x=binned["distance_bin_km"],
                                    y=binned["rssi_median"],
                                    mode="lines",
                                    name="Median RSSI",
                                    line=dict(width=3, color="#f97316"),
                                )
                            )
                        fig.update_layout(
                            height=420,
                            margin=dict(l=20, r=20, t=30, b=20),
                            showlegend=True,
                            legend=dict(orientation="h", x=0, y=1.02),
                            xaxis_title="Distance (km)",
                            yaxis_title="RSSI (dB)",
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.scatter_chart(data, x="distance_km", y="rssi_db")
                else:
                    st.info("RSSI vs distance data missing required columns.")
                st.dataframe(data.head(20), use_container_width=True)

    with section_altitude:
        st.subheader("Altitude vs distance")
        result = analysis_altitude_distance.analyze(
            packets_signal,
            station_lat=station_lat,
            station_lon=station_lon,
        )
        if not result.get("implemented"):
            st.info("Altitude vs distance analysis not implemented.")
        else:
            summary = result.get("summary") or {}
            data = result.get("data")
            if data is None or (hasattr(data, "empty") and data.empty) or (hasattr(data, "__len__") and len(data) == 0):
                st.info("No data available.")
            else:
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1:
                    st.metric("Packet total", fmt_int(summary.get("packet_total")))
                with c2:
                    val = summary.get("max_distance_km")
                    st.metric("Max distance (km)", f"{fmt_float(val, 1)}" if val is not None else "—")
                with c3:
                    val = summary.get("mean_altitude_m")
                    st.metric("Mean altitude (m)", f"{fmt_float(val, 0)}" if val is not None else "—")
                with c4:
                    val = summary.get("p95_distance_km")
                    st.metric("P95 distance (km)", f"{fmt_float(val, 1)}" if val is not None else "—")
                with c5:
                    st.empty()
                if "distance_km" in data.columns and "altitude_m" in data.columns:
                    if go is not None:
                        fig = go.Figure()
                        fig.add_trace(
                            go.Scatter(
                                x=data["distance_km"],
                                y=data["altitude_m"],
                                mode="markers",
                                name="Packets",
                                marker=dict(size=2, opacity=0.15),
                            )
                        )
                        # Feature 03 uses 20 km bins for altitude trend readability
                        bins = (data["distance_km"] // 20) * 20
                        med = (
                            data.assign(distance_bin_km=bins)
                            .groupby("distance_bin_km", as_index=False)
                            .agg(altitude_median=("altitude_m", "median"))
                            .sort_values("distance_bin_km")
                        )
                        if not med.empty:
                            fig.add_trace(
                                go.Scatter(
                                    x=med["distance_bin_km"],
                                    y=med["altitude_median"],
                                    mode="lines",
                                    name="Median altitude",
                                    line=dict(width=3, color="#0ea5e9"),
                                )
                            )
                        fig.update_layout(
                            height=420,
                            margin=dict(l=20, r=20, t=30, b=20),
                            showlegend=True,
                            legend=dict(orientation="h", x=0, y=1.02),
                            xaxis_title="Distance (km)",
                            yaxis_title="Altitude (m)",
                            # limit altitude axis for readability; extreme outliers remain in table/statistics
                            xaxis=dict(range=[0, 350]),
                            yaxis=dict(range=[0, 5000]),
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.scatter_chart(data, x="distance_km", y="altitude_m")
                binned = result.get("binned_data")
                if binned is not None and not binned.empty:
                    order = ["0-500 m", "500-1000 m", "1000-2000 m", ">2000 m"]
                    if "altitude_bin" in binned.columns:
                        binned = binned.copy()
                        binned["altitude_bin"] = pd.Categorical(binned["altitude_bin"], categories=order, ordered=True)
                        binned = binned.sort_values("altitude_bin")
                    st.dataframe(binned, use_container_width=True)

    with section_distribution:
        st.subheader("Distance distribution")
        result = analysis_station_range.analyze(df_grid)
        if not result.get("implemented"):
            st.info("Distance distribution analysis not implemented.")
        else:
            summary = result.get("summary") or {}
            data = result.get("data")
            if data is None or (hasattr(data, "empty") and data.empty) or (hasattr(data, "__len__") and len(data) == 0):
                st.info("No data available.")
            if summary:
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1:
                    st.metric("Packet total", fmt_int(summary.get("packet_total")))
                with c2:
                    st.metric("Grid cells", fmt_int(summary.get("grid_cells")))
                with c3:
                    val = summary.get("max_distance_km")
                    st.metric("Max distance (km)", f"{fmt_float(val, 1)}" if val is not None else "—")
                with c4:
                    val = summary.get("p95_distance_km")
                    st.metric("P95 distance (km)", f"{fmt_float(val, 1)}" if val is not None else "—")
                with c5:
                    st.empty()
            else:
                st.info("No distance statistics available.")


def render_rf_view() -> None:
    section_azimuth = st.container()
    section_summary = st.container()
    section_antenna = st.container()
    section_terrain = st.container()
    section_compare = st.container()
    section_probability = st.container()
    section_horizon = st.container()
    section_range = st.container()

    df_grid = load_coverage_grid(db_path, filters_apply["since_epoch"])
    quality_result = analysis_station_quality.analyze(df_grid)
    range_result = analysis_station_range.analyze(df_grid)
    packets_horizon = _load_packets_window_raw(
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
    horizon_result = analysis_radio_horizon.analyze(
        packets_horizon,
        station_lat=station_lat,
        station_lon=station_lon,
    )

    with section_azimuth:
        st.subheader("Azimuth radiation")
        result = analysis_polar.analyze(df_grid, station_lat=station_lat, station_lon=station_lon)
        if not result.get("implemented"):
            st.info("Azimuth radiation analysis not implemented.")
        else:
            data = result.get("data")
            summary = result.get("summary") or {}
            if data is None or (hasattr(data, "empty") and data.empty) or (hasattr(data, "__len__") and len(data) == 0):
                st.info("No data available.")
            else:
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1:
                    st.metric("Azimuth bins", fmt_int(summary.get("bins")))
                with c2:
                    st.metric("Packet total", fmt_int(summary.get("packet_total")))
                with c3:
                    val = summary.get("max_distance_km")
                    st.metric("Max distance (km)", f"{fmt_float(val, 1)}" if val is not None else "—")
                with c4:
                    val = summary.get("anisotropy_ratio")
                    st.metric("Anisotropy", f"{fmt_float(val, 2)}" if val is not None else "—")
                with c5:
                    st.empty()
                best_sector = summary.get("best_sector_deg")
                worst_sector = summary.get("worst_sector_deg")
                shadow_flag = summary.get("shadow_suspect")
                anisotropy_level = summary.get("anisotropy_level")
                st.caption(
                    f"Best sector: {fmt_float(best_sector, 0)}° • "
                    f"Worst sector: {fmt_float(worst_sector, 0)}° • "
                    f"Shadow suspect: {'yes' if shadow_flag else 'no'} • "
                    f"Anisotropy: {anisotropy_level or 'n/a'}"
                )
                if "azimuth_center_deg" in data.columns and "max_distance_km" in data.columns:
                    chart = data[["azimuth_center_deg", "max_distance_km"]].copy()
                    chart = chart.sort_values("azimuth_center_deg")
                    st.line_chart(
                        chart,
                        x="azimuth_center_deg",
                        y="max_distance_km",
                        height=240,
                    )
                st.dataframe(
                    data[
                        [
                            "azimuth_center_deg",
                            "packet_count",
                            "p95_distance_km",
                            "mean_rssi_db",
                        ]
                    ].head(20),
                    use_container_width=True,
                )

    with section_summary:
        st.subheader("Station synthesis")
        quality_score = (quality_result.get("summary") or {}).get("quality_score")
        if quality_score is None:
            health_status = "N/A"
        elif quality_score >= 80:
            health_status = "GOOD"
        elif quality_score >= 50:
            health_status = "FAIR"
        else:
            health_status = "POOR"

        p95_range = (range_result.get("summary") or {}).get("p95_distance_km")
        if p95_range is None:
            range_status = "N/A"
        elif p95_range < 100:
            range_status = "LOW"
        elif p95_range < 200:
            range_status = "NORMAL"
        else:
            range_status = "HIGH"

        efficiency_ratio = (horizon_result.get("summary") or {}).get("efficiency_ratio")
        if efficiency_ratio is None:
            horizon_status = "N/A"
        elif efficiency_ratio < 0.7:
            horizon_status = "LOW"
        elif efficiency_ratio < 1.1:
            horizon_status = "NORMAL"
        else:
            horizon_status = "HIGH"

        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.metric("Station health", health_status)
        with c2:
            st.metric("Range status", range_status)
        with c3:
            st.metric("Horizon status", horizon_status)
        with c4:
            st.empty()
        with c5:
            st.empty()

    with section_antenna:
        st.subheader("Antenna diagnostics")
        result = analysis_antenna_health.analyze(
            df_grid,
            station_lat=station_lat,
            station_lon=station_lon,
        )
        if not result.get("implemented"):
            st.info("Antenna diagnostics not implemented.")
        else:
            summary = result.get("summary") or {}
            data = result.get("data")
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                st.metric("Health status", summary.get("health_status") or "N/A")
            with c2:
                val = summary.get("anisotropy_ratio")
                st.metric("Anisotropy ratio", f"{fmt_float(val, 2)}" if val is not None else "—")
            with c3:
                shadow_flag = summary.get("suspected_shadow")
                st.metric("Suspected shadow", "yes" if shadow_flag else "no")
            with c4:
                val = summary.get("best_sector_deg")
                st.metric("Best sector (°)", f"{fmt_float(val, 0)}" if val is not None else "—")
            with c5:
                val = summary.get("worst_sector_deg")
                st.metric("Worst sector (°)", f"{fmt_float(val, 0)}" if val is not None else "—")
            if summary.get("suspected_shadow") is False:
                st.info("No significant directional shadow detected")
            if data is not None and not data.empty:
                cols = [
                    "azimuth_center_deg",
                    "packet_count",
                    "p95_distance_km",
                    "mean_rssi_db",
                ]
                st.dataframe(data[[c for c in cols if c in data.columns]].head(20), use_container_width=True)

    with section_terrain:
        st.subheader("Terrain analysis")
        result = analysis_terrain.analyze(
            df_grid,
            station_lat=station_lat,
            station_lon=station_lon,
        )
        if not result.get("implemented"):
            st.info("Terrain analysis not implemented.")
        else:
            summary = result.get("summary") or {}
            data = result.get("data")
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                st.metric("Terrain status", summary.get("terrain_status") or "N/A")
            with c2:
                st.metric("Open sectors", fmt_int(summary.get("open_sector_count")))
            with c3:
                st.metric("Limited sectors", fmt_int(summary.get("limited_sector_count")))
            with c4:
                val = summary.get("best_opening_deg")
                st.metric("Best opening (°)", f"{fmt_float(val, 0)}" if val is not None else "—")
            with c5:
                val = summary.get("main_limited_deg")
                st.metric("Main limited (°)", f"{fmt_float(val, 0)}" if val is not None else "—")
            d1, d2, d3, d4, d5 = st.columns(5)
            with d1:
                st.metric("Terrain mask", "yes" if summary.get("terrain_mask_suspected") else "no")
            with d2:
                st.empty()
            with d3:
                st.empty()
            with d4:
                st.empty()
            with d5:
                st.empty()
            if data is not None and not data.empty:
                cols = [
                    "azimuth_center_deg",
                    "packet_count",
                    "p95_distance_km",
                    "mean_rssi_db",
                    "terrain_class",
                ]
                chart_cols = ["azimuth_center_deg", "p95_distance_km"]
                if all(c in data.columns for c in chart_cols):
                    chart = data[chart_cols].sort_values("azimuth_center_deg")
                    st.line_chart(chart, x="azimuth_center_deg", y="p95_distance_km", height=220)
                st.dataframe(data[[c for c in cols if c in data.columns]].head(20), use_container_width=True)

    with section_compare:
        st.subheader("Station comparison")
        compare_map = _parse_compare_stations(os.getenv("OGN_COMPARE_STATIONS", ""))
        compare_map.setdefault(station_callsign, (station_lat, station_lon))
        packets_compare = _load_packets_window_raw(
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
        result = analysis_station_compare.analyze(
            packets_compare,
            station_coords=compare_map,
            station_callsigns=list(compare_map.keys()),
        )
        if not result.get("implemented"):
            summary = result.get("summary") or {}
            reason = summary.get("reason")
            if reason == "missing_station_config":
                st.info("Station comparison requires OGN_COMPARE_STATIONS with at least 2 stations.")
            elif reason == "fewer_than_two_stations":
                st.info("Station comparison requires at least 2 configured stations.")
            elif reason == "no_packets_for_configured_stations":
                st.info(
                    "Configured stations were found, but fewer than 2 have usable data in the selected time window."
                )
            elif reason == "invalid_station_coordinates":
                st.info("Some configured stations have missing or invalid coordinates.")
            else:
                st.info("Station comparison not implemented.")
            st.caption("Example: OGN_COMPARE_STATIONS=FK50887:47.3359,7.2728;STATION2:47.20,7.40")
            configured = summary.get("configured_station_count")
            comparable = summary.get("comparable_station_count")
            if configured is not None or comparable is not None:
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1:
                    st.metric("Configured stations", fmt_int(configured))
                with c2:
                    st.metric("Comparable stations", fmt_int(comparable))
                with c3:
                    st.empty()
                with c4:
                    st.empty()
                with c5:
                    st.empty()
        else:
            summary = result.get("summary") or {}
            data = result.get("data")
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                st.metric("Station count", fmt_int(summary.get("station_count")))
            with c2:
                st.metric("Best station", summary.get("best_station") or "—")
            with c3:
                val = summary.get("best_rank_score")
                st.metric("Best rank score", f"{fmt_float(val, 2)}" if val is not None else "—")
            with c4:
                st.empty()
            with c5:
                st.empty()
            if data is not None and not data.empty:
                if "station_callsign" in data.columns and "rank_score" in data.columns:
                    chart = data[["station_callsign", "rank_score"]].set_index("station_callsign")
                    st.bar_chart(chart)
                cols = [
                    "station_callsign",
                    "rank_score",
                    "p95_distance_km",
                    "max_distance_km",
                    "packet_total",
                    "quality_score",
                    "health_status",
                ]
                st.dataframe(data[[c for c in cols if c in data.columns]], use_container_width=True)

    with section_probability:
        st.subheader("Coverage probability")
        result = quality_result
        if not result.get("implemented"):
            st.info("Coverage probability analysis not implemented.")
        else:
            summary = result.get("summary") or {}
            data = result.get("data")
            if data is None or (hasattr(data, "empty") and data.empty) or (hasattr(data, "__len__") and len(data) == 0):
                st.info("No data available.")
            if summary:
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1:
                    st.metric("Packet total", fmt_int(summary.get("packet_total")))
                with c2:
                    val = summary.get("rssi_best")
                    st.metric("Best RSSI (dB)", f"{fmt_float(val, 1)}" if val is not None else "—")
                with c3:
                    val = summary.get("rssi_mean")
                    st.metric("Mean RSSI (dB)", f"{fmt_float(val, 1)}" if val is not None else "—")
                with c4:
                    val = summary.get("quality_score")
                    st.metric("Quality score", f"{fmt_float(val, 0)}" if val is not None else "—")
                with c5:
                    st.empty()
            else:
                st.info("No quality statistics available.")

    with section_horizon:
        st.subheader("Radio horizon")
        result = horizon_result
        if not result.get("implemented"):
            st.info("Radio horizon analysis not implemented.")
        else:
            summary = result.get("summary") or {}
            data = result.get("data")
            if data is None or (hasattr(data, "empty") and data.empty) or (hasattr(data, "__len__") and len(data) == 0):
                st.info("No data available.")
            else:
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1:
                    st.metric("Packet total", fmt_int(summary.get("packet_total")))
                with c2:
                    val = summary.get("horizon_mean_km")
                    st.metric("Horizon mean (km)", f"{fmt_float(val, 1)}" if val is not None else "—")
                with c3:
                    val = summary.get("horizon_p95_km")
                    st.metric("Horizon P95 (km)", f"{fmt_float(val, 1)}" if val is not None else "—")
                with c4:
                    val = summary.get("observed_p95_distance_km")
                    st.metric("Observed P95 (km)", f"{fmt_float(val, 1)}" if val is not None else "—")
                with c5:
                    val = summary.get("efficiency_ratio")
                    st.metric("Efficiency ratio", f"{fmt_float(val, 2)}" if val is not None else "—")
                station_alt_used = summary.get("station_alt_m")
                if station_alt_used is not None:
                    st.caption(f"Station altitude used: {fmt_float(station_alt_used, 0)} m")
                if "horizon_km" in data.columns and "distance_km" in data.columns:
                    if go is not None:
                        fig = go.Figure()
                        fig.add_trace(
                            go.Scatter(
                                x=data["horizon_km"],
                                y=data["distance_km"],
                                mode="markers",
                                name="Packets",
                                marker=dict(size=2, opacity=0.15),
                            )
                        )
                        fig.add_trace(
                            go.Scatter(
                                x=[0, 400],
                                y=[0, 400],
                                mode="lines",
                                name="Theoretical horizon",
                                line=dict(width=2, color="#f97316"),
                            )
                        )
                        med = result.get("binned_data")
                        if med is not None and "sample_count" in med.columns:
                            med = med[med["sample_count"] >= 30]
                        if med is not None and not med.empty:
                            fig.add_trace(
                                go.Scatter(
                                    x=med["horizon_bin_km"],
                                    y=med["distance_median"],
                                    mode="lines",
                                    name="Median observed",
                                    line=dict(width=3, color="#0ea5e9"),
                                )
                            )
                        fig.update_layout(
                            height=420,
                            margin=dict(l=20, r=20, t=30, b=20),
                            showlegend=True,
                            legend=dict(orientation="h", x=0, y=1.02),
                            xaxis_title="Horizon (km)",
                            yaxis_title="Distance (km)",
                            xaxis=dict(range=[0, 400]),
                            yaxis=dict(range=[0, 400]),
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.scatter_chart(data, x="horizon_km", y="distance_km")
                else:
                    st.info("Radio horizon data missing required columns.")

    with section_range:
        st.subheader("Station range estimation")
        result = range_result
        if not result.get("implemented"):
            st.info("Station range estimation not implemented.")
        else:
            summary = result.get("summary") or {}
            data = result.get("data")
            if data is None or (hasattr(data, "empty") and data.empty) or (hasattr(data, "__len__") and len(data) == 0):
                st.info("No data available.")
            if summary:
                c1, c2, c3, c4, c5 = st.columns(5)
                with c1:
                    st.metric("Packet total", fmt_int(summary.get("packet_total")))
                with c2:
                    st.metric("Grid cells", fmt_int(summary.get("grid_cells")))
                with c3:
                    val = summary.get("max_distance_km")
                    st.metric("Max distance (km)", f"{fmt_float(val, 1)}" if val is not None else "—")
                with c4:
                    val = summary.get("p95_distance_km")
                    st.metric("P95 distance (km)", f"{fmt_float(val, 1)}" if val is not None else "—")
                with c5:
                    st.empty()
            else:
                st.info("No range statistics available.")


def render_debug_view() -> None:
    section_raw = st.container()
    section_sql = st.container()
    section_stats = st.container()

    with section_raw:
        st.subheader("Raw packets")
        if not raw_packets_mode:
            st.info(
                "Raw packets disabled for performance.\n"
                "Enable in Advanced settings → Developer → Raw packets mode"
            )
        else:
            ctx = get_packets_context()
            result = analysis_station_compare.analyze(ctx.df_packets)
            if not result.get("implemented"):
                st.info("Feature not implemented yet")

    with section_sql:
        st.subheader("SQL info")
        st.info("Feature not implemented yet")

    with section_stats:
        st.subheader("Dataset statistics")
        result = analysis_station_quality.analyze(grid_df_kpi)
        if not result.get("implemented"):
            st.info("Feature not implemented yet")


with content_container:
    if view == "Coverage":
        render_coverage_view()
    elif view == "Signal":
        render_signal_view()
    elif view == "RF diagnostics":
        render_rf_view()
    elif view == "Debug":
        render_debug_view()
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
    grid_df = load_coverage_grid(db_path, filters_apply["since_epoch"])
    st.caption(
        f"Packets processed: {fmt_int(packets_received) if packets_received is not None else '—'} • "
        f"Grid cells: {fmt_int(len(grid_df)) if not grid_df.empty else '—'} • "
        f"Last update: {(last_ts[:19] + 'Z') if last_ts else '—'}"
    )
