#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
OGN / APRS-IS — Dashboard local (SQLite)

Objectifs:
- UI claire (wide), pas de régression (carte + signal-vs-distance quand data dispo)
- Robuste: tolère de petites variations de schéma (colonnes absentes)
- "Coverage" = paquets "heard-by" ta station (igate=FK50887 ou raw contient ",FK50887:")
- Performance: fenêtre temporelle + limite rows SQL + cache TTL

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
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st

from ogn_tool.config import get_config
from ogn_tool.db import connect
from ogn_tool.rf_analysis import compute_azimuth_stats, compute_distance_probability, reliable_distance_km

try:
    from streamlit_folium import st_folium
    import folium
    from folium.features import DivIcon
    from folium.plugins import HeatMap, MarkerCluster
except Exception as e:  # pragma: no cover
    st.error("Dépendance manquante: streamlit-folium / folium. Installe: pip install streamlit-folium folium")
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
# Tu as donné roof exact (Google Maps)
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
    "show_heatmap": False,
    "rings_km": [10, 25, 50, 100],
    "use_cov_grid": True,
    "map_mode": "Coverage grid",
    "point_size": 3,
    "limit_rows": 25000,
    "perf_cache": True,
    "map_max_points": 2000,
    "scatter_max_points": 1000,
    "debug_sql": False,
    "do_autorefresh": False,
    "show_cluster": False,
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
        current_mode = st.session_state["filters_edit"]["mode"]
        st.markdown("## Station")
        station_callsign = st.text_input("Callsign", st.session_state["filters_edit"]["station_callsign"])
        db_path = st.text_input("DB SQLite", st.session_state["filters_edit"]["db_path"])
        station_lat = st.number_input("Latitude", value=float(st.session_state["filters_edit"]["station_lat"]), format="%.6f")
        station_lon = st.number_input("Longitude", value=float(st.session_state["filters_edit"]["station_lon"]), format="%.6f")

        st.markdown("## Time window")
        hours = st.slider("Fenêtre temporelle (heures)", 1, 72, int(st.session_state["filters_edit"]["hours"]))

        st.markdown("## Data filters")
        source_mode = st.selectbox("Vue radio", ["Heard-by station", "Radio station view"], index=["Heard-by station", "Radio station view"].index(st.session_state["filters_edit"]["source_mode"]))
        dst_types = st.multiselect("Types", ["OGNFNT", "OGFLR", "OGFLR7", "OGNSDR", "OGNDVS"], default=st.session_state["filters_edit"]["dst_types"])
        only_heard_by = st.checkbox("Coverage heard-by", value=bool(st.session_state["filters_edit"]["only_heard_by"]))
        only_local_radio = st.checkbox("Uniquement radio locale", value=bool(st.session_state["filters_edit"]["only_local_radio"]))
        igate_filter = st.text_input("Filtre igate (optionnel)", value=st.session_state["filters_edit"]["igate_filter"])

        st.markdown("## Visualization")
        basemap_label = st.selectbox("Fond de carte", list(BASEMAPS.keys()), index=list(BASEMAPS.keys()).index(st.session_state["filters_edit"]["basemap_label"]))
        map_mode_options = [
            "Coverage grid",
            "Heatmap RSSI",
            "Heatmap distance",
            "Packets debug",
        ]
        prev_mode = st.session_state["filters_edit"]["map_mode"]
        if prev_mode not in map_mode_options:
            prev_mode = "Coverage grid"
        map_mode = st.selectbox("Mode carte", map_mode_options, index=map_mode_options.index(prev_mode))
        point_size = st.slider("Taille des points", 1, 10, int(st.session_state["filters_edit"]["point_size"]))
        show_rings = st.checkbox("Afficher anneaux de portée", value=bool(st.session_state["filters_edit"]["show_rings"]))
        show_heatmap = st.checkbox("Afficher heatmap couverture", value=bool(st.session_state["filters_edit"].get("show_heatmap", False)))
        show_cluster = st.checkbox("Cluster marqueurs (plus lent)", value=bool(st.session_state["filters_edit"].get("show_cluster", False)))
        use_cov_grid = st.checkbox("Utiliser coverage grid (rapide)", value=bool(st.session_state["filters_edit"].get("use_cov_grid", False)))
        rings_km = st.multiselect("Anneaux (km)", [5, 10, 25, 50, 75, 100, 150, 200], default=st.session_state["filters_edit"]["rings_km"])

        st.markdown("## Performance")
        limit_rows = st.slider("Max rows SQL", 1000, 50000, int(st.session_state["filters_edit"]["limit_rows"]))
        map_max_points = st.slider("Max points carte", 100, 5000, int(st.session_state["filters_edit"]["map_max_points"]))
        scatter_max_points = st.slider("Max points scatter", 100, 5000, int(st.session_state["filters_edit"]["scatter_max_points"]))
        do_autorefresh = st.checkbox("Auto-refresh (30s)", value=bool(st.session_state["filters_edit"]["do_autorefresh"]))

        if current_mode == "Expert":
            st.subheader("Maintenance DB")
            debug_sql = st.checkbox("Debug SQL (timings)", value=bool(st.session_state["filters_edit"]["debug_sql"]))
        else:
            debug_sql = False

        st.markdown("## Mode")
        mode = st.selectbox("Interface", ["Standard", "Avancé", "Expert"], index=["Standard", "Avancé", "Expert"].index(st.session_state["filters_edit"]["mode"]))

        apply_button = st.form_submit_button("▶ Appliquer les filtres")

    if current_mode == "Expert":
        st.subheader("Maintenance DB")
        safe_opt = st.button("ANALYZE / OPTIMIZE")
        vacuum_opt = st.button("VACUUM")
        create_idx = st.button("Créer index")
        if safe_opt:
            with st.spinner("Optimisation en cours..."):
                try:
                    optimize_db(st.session_state["filters_apply"]["db_path"], vacuum=False)
                    st.success("Optimisation terminée.")
                except Exception as e:
                    st.error(f"Échec optimisation: {e!r}")
        if vacuum_opt:
            with st.spinner("VACUUM en cours..."):
                try:
                    optimize_db(st.session_state["filters_apply"]["db_path"], vacuum=True)
                    st.success("VACUUM terminé.")
                except Exception as e:
                    st.error(f"Échec VACUUM: {e!r}")
        if create_idx:
            with st.spinner("Création des indexes..."):
                try:
                    create_indexes(st.session_state["filters_apply"]["db_path"])
                    st.success("Indexes créés.")
                except Exception as e:
                    st.error(f"Échec création indexes: {e!r}")

    if apply_button:
        st.session_state["filters_edit"] = {
            **st.session_state["filters_edit"],
            "mode": mode,
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
            "basemap_label": basemap_label,
            "map_mode": map_mode,
            "point_size": int(point_size),
            "show_rings": bool(show_rings),
            "show_heatmap": bool(show_heatmap),
            "show_cluster": bool(show_cluster),
            "use_cov_grid": bool(use_cov_grid),
            "rings_km": list(rings_km),
            "limit_rows": int(limit_rows),
            "map_max_points": int(map_max_points),
            "scatter_max_points": int(scatter_max_points),
            "do_autorefresh": bool(do_autorefresh),
            "debug_sql": bool(debug_sql),
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
show_heatmap = filters_apply.get("show_heatmap", False)
show_cluster = filters_apply.get("show_cluster", False)
use_cov_grid = filters_apply.get("use_cov_grid", False)
rings_km = filters_apply["rings_km"]
map_mode = filters_apply["map_mode"]
point_size = filters_apply["point_size"]
limit_rows = filters_apply["limit_rows"]
perf_cache = filters_apply["perf_cache"]
map_max_points = filters_apply["map_max_points"]
scatter_max_points = filters_apply["scatter_max_points"]
debug_sql = filters_apply["debug_sql"]
do_autorefresh = filters_apply["do_autorefresh"]
btn_refresh = False

if do_autorefresh:
    st.caption("Auto-refresh actif (30s)")
    _set_query_ts(str(int(dt.datetime.now().timestamp())))
    _autorefresh(interval_ms=30000, key="autorefresh_30s")

query_log: List[Dict] = []
if debug_sql:
    rows_total, last_ts = _db_meta_raw(db_path, query_log=query_log)
else:
    rows_total, last_ts = db_meta(db_path)

# Title + station summary
st.header("OGN RF Coverage Analyzer")
st.caption(f"Station {station_callsign} • APRS-IS / OGN analysis")
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

if fresh_state == "ok":
    st.success("🟢 Database live")
elif fresh_state == "warn":
    st.warning(f"🟠 Database slow (last packet {int(age_s)}s)")
elif fresh_state == "err":
    st.error(f"🔴 Database offline (last packet {int(age_s)}s)")
else:
    st.info("ℹ️ Database status unknown")

# Header KPIs (lightweight)
cols = st.columns(3)
with cols[0]:
    st.metric("Rows DB", fmt_int(rows_total))
with cols[1]:
    st.metric("Last packet (UTC)", (last_ts[:19] + "Z") if last_ts else "—")
with cols[2]:
    st.metric("Packets in window", "—")

apply_ts = st.session_state.get("last_apply_ts")
apply_time = apply_ts.strftime("%H:%M:%S") if apply_ts else "—"
types_str = "/".join(dst_types) if dst_types else "—"
st.info(f"Filters applied: Station={station_callsign} | Window={hours}h | Types={types_str} | Mode={mode} — Last apply: {apply_time}")

ctx_hash = _filters_hash(filters_apply)
cached_ctx = st.session_state.get("analysis_ctx")
cached_hash = st.session_state.get("analysis_ctx_hash")
if cached_ctx is not None and cached_hash == ctx_hash:
    ctx = cached_ctx
else:
    with st.status("Chargement des données", expanded=False) as status:
        ctx = build_context(filters_apply, query_log=query_log if debug_sql else None)
        status.update(label="Données chargées", state="complete")
    st.session_state["analysis_ctx"] = ctx
    st.session_state["analysis_ctx_hash"] = ctx_hash

analysis_context = {
    "filters": filters_apply,
    "dataframe": ctx.df_packets,
    "metrics": ctx.metrics,
}

# Precompute coverage probability KPIs (fast on grid)
grid_df_kpi = load_coverage_grid(db_path, filters_apply["since_epoch"])
d90 = d50 = d10 = None
if not grid_df_kpi.empty:
    dist_bins_kpi = pd.to_numeric(grid_df_kpi.get("max_distance_km", pd.Series(dtype=float)), errors="coerce").to_numpy()
    pkt_bins_kpi = pd.to_numeric(grid_df_kpi.get("packet_count", pd.Series(dtype=float)), errors="coerce").to_numpy()
    centers_kpi, probs_kpi = compute_distance_probability(dist_bins_kpi, pkt_bins_kpi, bin_size_km=5.0)
    if centers_kpi.size > 0:
        d90 = reliable_distance_km(centers_kpi, probs_kpi, threshold=0.9)
        d50 = reliable_distance_km(centers_kpi, probs_kpi, threshold=0.5)
        d10 = reliable_distance_km(centers_kpi, probs_kpi, threshold=0.1)

# Update packets window KPI
cols[2].metric("Packets in window", fmt_int(analysis_context["metrics"].get("rows_window")))

# KPI bar
colA, colB, colC, colD, colE = st.columns(5)
with colA:
    st.metric("Max distance", f"{fmt_float(analysis_context['metrics'].get('max_distance_km'), 1)} km")
with colB:
    st.metric("P95 distance", f"{fmt_float(analysis_context['metrics'].get('p95_distance_km'), 1)} km")
with colC:
    st.metric("Reliable (90%)", f"{fmt_float(d90, 1)} km" if d90 is not None else "—")
with colD:
    st.metric("Median (50%)", f"{fmt_float(d50, 1)} km" if d50 is not None else "—")
with colE:
    st.metric("Fringe (10%)", f"{fmt_float(d10, 1)} km" if d10 is not None else "—")

# Lazy view selector (avoids running all tabs)
view = st.segmented_control(
    "View",
    [
        "Coverage map",
        "Signal vs distance",
        "Distance distribution",
        "Coverage probability",
        "RF analysis",
        "Debug",
    ],
    default="Coverage map",
)


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


def render_map() -> None:
    with st.container():
        st.subheader("Coverage map")
        with st.spinner("Loading map..."):
            bm = BASEMAPS[basemap_label]
            m = folium.Map(
                location=[station_lat, station_lon],
                zoom_start=8,
                tiles=None,
                control_scale=True,
                prefer_canvas=True,
            )
            folium.TileLayer(tiles=bm.tiles, attr=bm.attr, name=bm.name, control=False).add_to(m)
            folium.CircleMarker(
                location=[station_lat, station_lon],
                radius=7,
                weight=2,
                color="#000000",
                fill=True,
                fill_opacity=1.0,
                popup=f"{station_callsign} (ref)",
            ).add_to(m)
            max_range_km = analysis_context["metrics"].get("max_distance_km")
            max_range_label = fmt_float(max_range_km, 1)
            folium.Marker(
                location=[station_lat, station_lon],
                icon=DivIcon(
                    icon_size=(200, 36),
                    icon_anchor=(0, -10),
                    html=(
                        '<div style="font-size:12px;color:#111;background:rgba(255,255,255,0.8);'
                        'padding:2px 6px;border-radius:4px;border:1px solid #ddd;">'
                        f"Max range: {max_range_label} km</div>"
                    ),
                ),
            ).add_to(m)
            if show_rings and rings_km:
                for rkm in sorted(set(rings_km)):
                    folium.Circle(
                        location=[station_lat, station_lon],
                        radius=float(rkm) * 1000.0,
                        color="#3b82f6",
                        weight=1,
                        fill=False,
                        opacity=0.6,
                    ).add_to(m)
            use_packets = (map_mode == "Packets debug")
            if use_cov_grid and not use_packets:
                df_points = load_coverage_grid(db_path, filters_apply["since_epoch"])
            else:
                df_points = analysis_context["dataframe"].copy()
            if "lat" not in df_points.columns or "lon" not in df_points.columns:
                st.warning("⚠ Coverage grid introuvable ou invalide (colonnes lat/lon manquantes).")
                st_folium(m, height=750, use_container_width=True)
                return
            df_points = df_points[df_points["lat"].notna() & df_points["lon"].notna()]
            if df_points.empty:
                st.warning("⚠ Aucun paquet dans cette fenêtre temporelle.")
                st_folium(m, height=750, use_container_width=True)
                return
            max_cells_display = min(3000, map_max_points)
            if len(df_points) > max_cells_display:
                df_points = df_points.sample(n=max_cells_display, random_state=1)
            if show_heatmap and not df_points.empty:
                heat_data = df_points[["lat", "lon"]].dropna().values.tolist()
                HeatMap(
                    heat_data,
                    radius=12,
                    blur=18,
                    min_opacity=0.2,
                ).add_to(m)
            if not df_points.empty:
                if map_mode == "Heatmap RSSI":
                    col_db = "best_rssi_db" if use_cov_grid else "rx_db"
                    v = pd.to_numeric(df_points.get(col_db, pd.Series(dtype=float)), errors="coerce")
                    vmin = float(np.nanpercentile(v.to_numpy(), 10)) if v.notna().any() else -120.0
                    vmax = float(np.nanpercentile(v.to_numpy(), 90)) if v.notna().any() else -60.0
                    key = col_db
                    label = "dB"
                elif map_mode == "Heatmap distance":
                    col_dist = "max_distance_km" if use_cov_grid else "distance_km"
                    v = pd.to_numeric(df_points.get(col_dist, pd.Series(dtype=float)), errors="coerce")
                    vmin = float(np.nanpercentile(v.to_numpy(), 10)) if v.notna().any() else 0.0
                    vmax = float(np.nanpercentile(v.to_numpy(), 90)) if v.notna().any() else 50.0
                    key = col_dist
                    label = "km"
                elif map_mode == "Coverage grid":
                    col_dist = "max_distance_km" if use_cov_grid else "distance_km"
                    v = pd.to_numeric(df_points.get(col_dist, pd.Series(dtype=float)), errors="coerce")
                    vmin = float(np.nanpercentile(v.to_numpy(), 10)) if v.notna().any() else 0.0
                    vmax = float(np.nanpercentile(v.to_numpy(), 90)) if v.notna().any() else 50.0
                    key = col_dist
                    label = "km"
                else:
                    col_dist = "distance_km"
                    v = pd.to_numeric(df_points.get(col_dist, pd.Series(dtype=float)), errors="coerce")
                    vmin = float(np.nanpercentile(v.to_numpy(), 10)) if v.notna().any() else 0.0
                    vmax = float(np.nanpercentile(v.to_numpy(), 90)) if v.notna().any() else 50.0
                    key = col_dist
                    label = "km"

                vals = pd.to_numeric(df_points.get(key, pd.Series(dtype=float)), errors="coerce").to_numpy()
                colors = [
                    _color_from_value(float(val), vmin, vmax) if val == val else "#999999"
                    for val in vals
                ]
                layer = m
                if show_cluster and use_packets:
                    layer = MarkerCluster().add_to(m)
                for (lat, lon, src, dst, igate, ts, val, c) in zip(
                    df_points["lat"].to_numpy(),
                    df_points["lon"].to_numpy(),
                    df_points.get("src", pd.Series([""] * len(df_points))).to_numpy(),
                    df_points.get("dst", pd.Series([""] * len(df_points))).to_numpy(),
                    df_points.get("igate", pd.Series([""] * len(df_points))).to_numpy(),
                    df_points.get("ts_utc", pd.Series([""] * len(df_points))).to_numpy(),
                    vals,
                    colors,
                ):
                    popup = (
                        f"src={src}\n"
                        f"dst={dst}\n"
                        f"igate={igate}\n"
                        f"{label}={fmt_float(float(val) if val == val else None, 1)}\n"
                        f"ts={ts}"
                    )
                    radius = 4.0 if map_mode in ("Heatmap RSSI", "Heatmap distance", "Coverage grid") and not use_packets else float(point_size)
                    folium.CircleMarker(
                        location=[float(lat), float(lon)],
                        radius=radius,
                        weight=1,
                        color=c,
                        fill=True,
                        fill_opacity=0.75,
                        popup=popup,
                    ).add_to(layer)
            st_folium(m, height=750, use_container_width=True)


def render_scatter() -> None:
    st.subheader("Received signal strength vs distance")
    if analysis_context["dataframe"].empty:
        st.warning("⚠ Aucun paquet dans cette fenêtre temporelle.")
        return
    with st.spinner("Chargement scatter..."):
        df_sd = analysis_context["dataframe"].copy()
        df_sd["rx_db"] = pd.to_numeric(df_sd["rx_db"], errors="coerce")
        df_sd["distance_km"] = pd.to_numeric(df_sd.get("distance_km", np.nan), errors="coerce")
        df_sd = df_sd[df_sd["rx_db"].notna() & df_sd["distance_km"].notna()]
        max_points = min(2000, scatter_max_points)
        if len(df_sd) > max_points:
            df_sd = df_sd.sample(n=max_points, random_state=1)
        if df_sd.empty:
            st.warning("Aucun point avec dB + distance.")
        else:
            import matplotlib.pyplot as plt
            plt.style.use("seaborn-v0_8")
            fig = plt.figure(figsize=(10, 4))
            plt.scatter(df_sd["distance_km"].to_numpy(), df_sd["rx_db"].to_numpy(), s=14, alpha=0.65)
            plt.title("Received signal strength vs distance", fontsize=16)
            plt.xlabel("Distance (km)")
            plt.ylabel("Signal (dB)")
            plt.grid(alpha=0.3)
            st.pyplot(fig, clear_figure=True, use_container_width=True)


def render_histogram() -> None:
    st.subheader("Distance distribution")
    if analysis_context["dataframe"].empty:
        st.warning("⚠ Aucun paquet dans cette fenêtre temporelle.")
        return
    with st.spinner("Chargement histogramme..."):
        dist = pd.to_numeric(analysis_context["dataframe"].get("distance_km", pd.Series(dtype=float)), errors="coerce").dropna()
        if dist.empty:
            st.warning("Aucune distance disponible.")
        else:
            import matplotlib.pyplot as plt
            plt.style.use("seaborn-v0_8")
            fig = plt.figure(figsize=(10, 4))
            plt.hist(dist.to_numpy(), bins=40, alpha=0.7)
            plt.xlabel("Distance (km)")
            plt.ylabel("Packet count")
            plt.title("Distance distribution", fontsize=16)
            plt.grid(alpha=0.3)
            st.pyplot(fig, clear_figure=True, use_container_width=True)


def render_rf_analysis() -> None:
    st.subheader("RF azimuth analysis")
    df_grid = load_coverage_grid(db_path, filters_apply["since_epoch"])
    if df_grid.empty:
        st.warning("⚠ Coverage grid vide. Lance d'abord le build de la grille.")
        return
    with st.spinner("Calcul du diagramme RF..."):
        lat = pd.to_numeric(df_grid["lat"], errors="coerce")
        lon = pd.to_numeric(df_grid["lon"], errors="coerce")
        max_dist = pd.to_numeric(df_grid["max_distance_km"], errors="coerce")
        best_rssi = pd.to_numeric(df_grid.get("best_rssi_db", pd.Series(dtype=float)), errors="coerce")
        mask = lat.notna() & lon.notna() & max_dist.notna()
        if not mask.any():
            st.warning("Aucune cellule valide pour le diagramme.")
            return
        lat = lat[mask]
        lon = lon[mask]
        max_dist = max_dist[mask]
        best_rssi = best_rssi[mask]

        stats = compute_azimuth_stats(
            station_lat=station_lat,
            station_lon=station_lon,
            lat=lat.to_numpy(),
            lon=lon.to_numpy(),
            max_distance_km=max_dist.to_numpy(),
            best_rssi_db=best_rssi.to_numpy() if best_rssi.notna().any() else None,
            packet_count=df_grid.get("packet_count", pd.Series(dtype=float)).to_numpy()
            if "packet_count" in df_grid.columns
            else None,
            bin_size_deg=5.0,
        )

        import matplotlib.pyplot as plt

        import matplotlib.pyplot as plt
        plt.style.use("seaborn-v0_8")
        fig = plt.figure(figsize=(7, 4.2))
        ax = fig.add_subplot(111, polar=True)
        ax.plot(stats.angles_rad, stats.max_distance_km, linewidth=2, label="Max")
        ax.plot(stats.angles_rad, stats.p90_distance_km, linewidth=2, linestyle="--", label="P90")
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        ax.set_title("Portée par azimut (km) — max & P90")
        ax.legend(loc="upper right")
        st.pyplot(fig, clear_figure=True, use_container_width=True)

        if np.isfinite(stats.best_rssi_db).any():
            fig2 = plt.figure(figsize=(7, 4.2))
            ax2 = fig2.add_subplot(111, polar=True)
            ax2.plot(stats.angles_rad, stats.best_rssi_db, linewidth=2, color="#ef4444")
            ax2.set_theta_zero_location("N")
            ax2.set_theta_direction(-1)
            ax2.set_title("Meilleur RSSI par azimut (dB)")
            st.pyplot(fig2, clear_figure=True, use_container_width=True)

        if np.isfinite(stats.packet_count).any():
            fig3 = plt.figure(figsize=(7, 4.2))
            ax3 = fig3.add_subplot(111, polar=True)
            ax3.plot(stats.angles_rad, stats.packet_count, linewidth=2, color="#22c55e")
            ax3.set_theta_zero_location("N")
            ax3.set_theta_direction(-1)
            ax3.set_title("Densité de trafic par azimut (packets)")
            st.pyplot(fig3, clear_figure=True, use_container_width=True)


def render_debug() -> None:
    st.subheader("Debug")
    if analysis_context["dataframe"].empty:
        st.info("Aucune donnée.")
    else:
        with st.spinner("Chargement debug..."):
            top_src = analysis_context["dataframe"]["src"].value_counts().head(15).rename_axis("src").reset_index(name="count")
            st.dataframe(top_src, width="stretch", height=360)
            ig = analysis_context["dataframe"]["igate"].replace("", np.nan).dropna()
            top_ig = ig.value_counts().head(15).rename_axis("igate").reset_index(name="count")
            st.dataframe(top_ig, width="stretch", height=360)
    with st.expander("Pipeline info", expanded=False):
        st.json({
            "rows_total_db": rows_total,
            "last_ts": last_ts,
            "since_iso": filters_apply.get("since_iso"),
            "hours": hours,
            "dst_types": dst_types,
            "source_mode": source_mode,
            "limit_rows": limit_rows,
        })
    if debug_sql and query_log:
        st.dataframe(pd.DataFrame(query_log), width="stretch", height=240)


def render_coverage_probability() -> None:
    st.subheader("Coverage probability")
    df_grid = load_coverage_grid(db_path, filters_apply["since_epoch"])
    if df_grid.empty:
        st.warning("⚠ Coverage grid vide. Lance d'abord le build de la grille.")
        return
    dist_bins = pd.to_numeric(df_grid.get("max_distance_km", pd.Series(dtype=float)), errors="coerce").to_numpy()
    pkt_bins = pd.to_numeric(df_grid.get("packet_count", pd.Series(dtype=float)), errors="coerce").to_numpy()
    centers, probs = compute_distance_probability(dist_bins, pkt_bins, bin_size_km=5.0)
    if centers.size == 0:
        st.warning("Aucune donnée de probabilité.")
        return
    d90 = reliable_distance_km(centers, probs, threshold=0.9)
    d50 = reliable_distance_km(centers, probs, threshold=0.5)
    d10 = reliable_distance_km(centers, probs, threshold=0.1)

    import matplotlib.pyplot as plt
    plt.style.use("seaborn-v0_8")
    fig = plt.figure(figsize=(10, 4))
    ax = fig.add_subplot(111)
    ax.plot(centers, probs, linewidth=2)
    ax.set_ylim(0, 1.0)
    ax.set_xlabel("Distance (km)")
    ax.set_ylabel("Reception probability")
    ax.set_title("Coverage probability by distance", fontsize=16)
    ax.grid(alpha=0.3)
    ax.axhline(0.9, color="#f59e0b", linestyle="--", linewidth=1)
    ax.axhline(0.5, color="#22c55e", linestyle="--", linewidth=1)
    ax.axhline(0.1, color="#ef4444", linestyle="--", linewidth=1)
    st.pyplot(fig, clear_figure=True, use_container_width=True)


if view == "Coverage map":
    render_map()
elif view == "Signal vs distance":
    render_scatter()
elif view == "Distance distribution":
    render_histogram()
elif view == "Coverage probability":
    render_coverage_probability()
elif view == "RF analysis":
    render_rf_analysis()
elif view == "Debug":
    render_debug()
if _PROFILER:
    _PROFILER.disable()
    st.caption("Profiling actif (résultats affichés dans la console).")
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
        f"Packets processed: {fmt_int(analysis_context['metrics'].get('rows_window'))} • "
        f"Grid cells: {fmt_int(len(grid_df)) if not grid_df.empty else '—'} • "
        f"Last update: {(last_ts[:19] + 'Z') if last_ts else '—'}"
    )
