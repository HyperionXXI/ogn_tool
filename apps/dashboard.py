#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
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
import math
import os
import re
import sqlite3
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st

from ogn_tool.config import get_config
from ogn_tool.db import connect

try:
    from streamlit_folium import st_folium
    import folium
except Exception as e:  # pragma: no cover
    st.error("Dépendance manquante: streamlit-folium / folium. Installe: pip install streamlit-folium folium")
    raise

# ---------------------------
# Config & helpers
# ---------------------------

st.set_page_config(
    page_title="OGN / APRS-IS — Dashboard local",
    layout="wide",
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

@st.cache_data(ttl=5, show_spinner=False)
def db_meta(db_path: str) -> Tuple[int, Optional[str]]:
    """Return (rows_total, max_ts_utc) from packets table, robust."""
    if not os.path.exists(db_path):
        return 0, None
    con = sqlite3.connect(db_path)
    try:
        rows_total = con.execute("SELECT COUNT(*) FROM packets").fetchone()[0]
        max_ts = con.execute("SELECT MAX(ts_utc) FROM packets").fetchone()[0]
        return int(rows_total), max_ts
    finally:
        con.close()


def _build_where(
    since_iso: str,
    dst_types: List[str],
    station_callsign: str,
    only_heard_by: bool,
    igate_filter: str,
) -> Tuple[str, List]:
    # Normalise ts_utc:
    # - si "...Z" => "...+00:00"
    # Comparaison texte OK si tout est homogène.
    ts_norm = "(CASE WHEN substr(ts_utc,-1)='Z' THEN substr(ts_utc,1,length(ts_utc)-1)||'+00:00' ELSE ts_utc END)"

    where = [f"{ts_norm} >= ?"]
    params: List = [since_iso]  # since_iso DOIT être en +00:00

    if dst_types:
        where.append("dst IN ({})".format(",".join(["?"] * len(dst_types))))
        params.extend(dst_types)

    if igate_filter.strip():
        where.append("igate = ?")
        params.append(igate_filter.strip())

    if only_heard_by:
        where.append("(igate = ? OR raw LIKE ?)")
        params.append(station_callsign)
        params.append(f"%,{station_callsign}:%")

    return " AND ".join(where), params


@st.cache_data(ttl=5, show_spinner=False)
def load_packets_window(
    db_path: str,
    since_iso: str,
    dst_types: List[str],
    station_callsign: str,
    only_heard_by: bool,
    igate_filter: str,
    limit_rows: int,
) -> pd.DataFrame:
    if not os.path.exists(db_path):
        return pd.DataFrame()

    where_sql, params = _build_where(
        since_iso=since_iso,
        dst_types=dst_types,
        station_callsign=station_callsign,
        only_heard_by=only_heard_by,
        igate_filter=igate_filter,
    )

    sql = f"""
    SELECT
        ts_utc, src, dst, igate, qas, lat, lon, raw
    FROM packets
    WHERE {where_sql}
    ORDER BY ts_utc DESC
    LIMIT ?
    """
    params2 = params + [int(limit_rows)]

    con = sqlite3.connect(db_path)
    try:
        df = pd.read_sql_query(sql, con, params=params2)
    finally:
        con.close()

    return df


# ---------------------------
# UI
# ---------------------------

with st.sidebar:
    st.markdown("## Paramètres")

    db_path = st.text_input("DB SQLite", DB_DEFAULT)
    station_callsign = st.text_input("Station callsign", CALLSIGN_DEFAULT)

    st.markdown("### Station (référence)")
    station_lat = st.number_input("Station lat", value=float(ROOF_LAT_DEFAULT), format="%.6f")
    station_lon = st.number_input("Station lon", value=float(ROOF_LON_DEFAULT), format="%.6f")

    st.markdown("### Fenêtre / filtres")
    hours = st.slider("Fenêtre temporelle (heures)", min_value=1, max_value=48, value=6, step=1)

    dst_types = st.multiselect(
        "Types (dst)",
        options=["OGNFNT", "OGFLR", "OGFLR7", "OGNSDR", "OGNDVS"],
        default=["OGNFNT", "OGFLR", "OGFLR7"],
    )

    igate_filter = st.text_input("Filtre igate (optionnel)", value="")

    only_heard_by = st.checkbox(f"Coverage: uniquement 'heard-by {station_callsign}'", value=True)

    st.markdown("### Carte")
    basemap_label = st.selectbox("Fond de carte", options=list(BASEMAPS.keys()), index=0)
    show_rings = st.checkbox("Afficher anneaux de portée", value=True)
    rings_km = st.multiselect("Anneaux (km)", options=[5, 10, 25, 50, 75, 100, 150, 200], default=[10, 25, 50, 100])

    map_mode = st.selectbox("Mode carte", options=["Points (couleur = distance)", "Points (couleur = dB)"], index=0)
    point_size = st.slider("Taille points (px)", min_value=2, max_value=12, value=4, step=1)

    st.markdown("### Performance")
    limit_rows = st.slider("Max rows (SQL)", min_value=2000, max_value=100000, value=25000, step=1000)

    st.markdown("### Rafraîchissement")
    do_autorefresh = st.checkbox("Auto-refresh (5s)", value=False)
    btn_refresh = st.button("Refresh maintenant")

# Auto refresh
if do_autorefresh:
    st.caption("Auto-refresh actif (5s)")
    st.experimental_set_query_params(_ts=str(int(dt.datetime.now().timestamp())))
    st.autorefresh(interval=5000, key="autorefresh_5s")

if btn_refresh:
    st.cache_data.clear()

# Header / meta
rows_total, last_ts = db_meta(db_path)
st.title("OGN / APRS-IS — Dashboard local")

sub = f"Station: **{station_callsign}** — ref ({station_lat:.6f}, {station_lon:.6f}) — DB: `{db_path}`"
st.markdown(sub)

# DB freshness banner
fresh_state = "unknown"
age_s = None
if last_ts:
    try:
        # last_ts stored as ISO with +00:00
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
    st.success("DB vivante", icon="✅")
elif fresh_state == "warn":
    st.warning(f"DB potentiellement ralentie (dernier paquet il y a {int(age_s)}s)", icon="⚠️")
elif fresh_state == "err":
    st.error(f"DB possiblement figée (dernier paquet il y a {int(age_s)}s)", icon="🧊")
else:
    st.info("État DB: inconnu (timestamp non parsable).", icon="ℹ️")

# Load data window
since = now_utc() - dt.timedelta(hours=int(hours))
since_iso = since.isoformat().replace("+00:00", "+00:00")

df = load_packets_window(
    db_path=db_path,
    since_iso=since_iso,
    dst_types=dst_types,
    station_callsign=station_callsign,
    only_heard_by=only_heard_by,
    igate_filter=igate_filter,
    limit_rows=limit_rows,
)

# Compute derived fields (safe)
if not df.empty:
    # Ensure types
    df["lat"] = pd.to_numeric(safe_col(df, "lat"), errors="coerce")
    df["lon"] = pd.to_numeric(safe_col(df, "lon"), errors="coerce")
    df["rx_db"] = safe_col(df, "raw").apply(parse_db_from_raw)
    # distance for rows with coords
    mask_ll = df["lat"].notna() & df["lon"].notna()
    df.loc[mask_ll, "distance_km"] = haversine_km(station_lat, station_lon, df.loc[mask_ll, "lat"].to_numpy(), df.loc[mask_ll, "lon"].to_numpy())
else:
    df["rx_db"] = []
    df["distance_km"] = []

# Metrics row
colA, colB, colC, colD, colE, colF = st.columns([1.1, 1.3, 1.2, 1.1, 1.1, 1.1])

with colA:
    st.metric("Rows DB", fmt_int(rows_total))
with colB:
    st.metric("Dernier paquet (UTC)", (last_ts[:19] + "Z") if last_ts else "—")
with colC:
    st.metric("Chargés (SQL)", fmt_int(len(df)))
with colD:
    # If only_heard_by, df already filtered; else show 0 / unknown
    if only_heard_by:
        st.metric("Après heard-by", fmt_int(len(df)))
    else:
        st.metric("Après heard-by", "—")
with colE:
    max_km = float(df["distance_km"].max()) if "distance_km" in df.columns and df["distance_km"].notna().any() else None
    st.metric("Distance max (km)", fmt_float(max_km, 1))
with colF:
    p95 = float(np.nanpercentile(df["distance_km"].to_numpy(), 95)) if "distance_km" in df.columns and df["distance_km"].notna().any() else None
    st.metric("Distance P95 (km)", fmt_float(p95, 1))

st.divider()

tabs = st.tabs(["Couverture", "Signal vs Distance", "Debug"])

# ---------------------------
# Couverture tab (map)
# ---------------------------
with tabs[0]:
    st.subheader("Carte")

    if df.empty:
        st.info("Aucune donnée dans cette fenêtre / filtres.")
    else:
        bm = BASEMAPS[basemap_label]
        # Center map on station
        m = folium.Map(
            location=[station_lat, station_lon],
            zoom_start=8,
            tiles=None,  # IMPORTANT: avoid default tiles (which can override)
            control_scale=True,
        )
        folium.TileLayer(
            tiles=bm.tiles,
            attr=bm.attr,
            name=bm.name,
            control=False,
        ).add_to(m)

        # Station marker
        folium.CircleMarker(
            location=[station_lat, station_lon],
            radius=7,
            weight=2,
            color="#000000",
            fill=True,
            fill_opacity=1.0,
            popup=f"{station_callsign} (ref)",
        ).add_to(m)

        # Rings
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

        # Points
        # Choose coloring
        df_points = df.copy()
        df_points = df_points[df_points["lat"].notna() & df_points["lon"].notna()]

        if df_points.empty:
            st.warning("Pas de points avec lat/lon dans cette fenêtre.")
        else:
            # color scale (simple, stable)
            if map_mode == "Points (couleur = dB)":
                v = pd.to_numeric(df_points["rx_db"], errors="coerce")
                vmin = float(np.nanpercentile(v.to_numpy(), 10)) if v.notna().any() else 0.0
                vmax = float(np.nanpercentile(v.to_numpy(), 90)) if v.notna().any() else 30.0
                key = "rx_db"
                label = "dB"
            else:
                v = pd.to_numeric(df_points["distance_km"], errors="coerce")
                vmin = float(np.nanpercentile(v.to_numpy(), 10)) if v.notna().any() else 0.0
                vmax = float(np.nanpercentile(v.to_numpy(), 90)) if v.notna().any() else 50.0
                key = "distance_km"
                label = "km"

            def color_for(val: float) -> str:
                if val is None or (isinstance(val, float) and math.isnan(val)):
                    return "#999999"
                # normalize
                if vmax <= vmin:
                    t = 0.5
                else:
                    t = (val - vmin) / (vmax - vmin)
                    t = max(0.0, min(1.0, t))
                # blue -> cyan -> green -> yellow -> red (stable)
                if t < 0.25:
                    return "#2563eb"
                if t < 0.5:
                    return "#06b6d4"
                if t < 0.75:
                    return "#22c55e"
                if t < 0.9:
                    return "#eab308"
                return "#ef4444"

            # Add markers
            for _, r in df_points.head(20000).iterrows():
                val = r.get(key, None)
                c = color_for(float(val)) if val is not None and val == val else "#999999"
                popup = (
                    f"src={r.get('src','')}\n"
                    f"dst={r.get('dst','')}\n"
                    f"igate={r.get('igate','')}\n"
                    f"{label}={fmt_float(float(val) if val==val else None, 1)}\n"
                    f"ts={r.get('ts_utc','')}"
                )
                folium.CircleMarker(
                    location=[float(r["lat"]), float(r["lon"])],
                    radius=float(point_size),
                    weight=1,
                    color=c,
                    fill=True,
                    fill_opacity=0.75,
                    popup=popup,
                ).add_to(m)

            st_folium(m, width="stretch", height=520)

# ---------------------------
# Signal vs distance tab
# ---------------------------
with tabs[1]:
    st.subheader("Signal vs Distance")

    # Need dB + distance
    if df.empty:
        st.info("Aucune donnée dans cette fenêtre / filtres.")
    else:
        df_sd = df.copy()
        df_sd["rx_db"] = pd.to_numeric(df_sd["rx_db"], errors="coerce")
        df_sd["distance_km"] = pd.to_numeric(df_sd.get("distance_km", np.nan), errors="coerce")

        df_sd = df_sd[df_sd["rx_db"].notna() & df_sd["distance_km"].notna()]

        if df_sd.empty:
            st.warning("Aucun point avec dB + lat/lon (donc distance) dans cette fenêtre.")
        else:
            import matplotlib.pyplot as plt

            fig = plt.figure()
            plt.scatter(df_sd["distance_km"].to_numpy(), df_sd["rx_db"].to_numpy(), s=14, alpha=0.65)
            plt.title("RX signal vs distance")
            plt.xlabel("Distance (km)")
            plt.ylabel("Signal (dB)")
            st.pyplot(fig, clear_figure=True, use_container_width=True)

            # stats row
            p10 = float(np.nanpercentile(df_sd["rx_db"].to_numpy(), 10))
            p50 = float(np.nanpercentile(df_sd["rx_db"].to_numpy(), 50))
            p90 = float(np.nanpercentile(df_sd["rx_db"].to_numpy(), 90))
            mx = float(np.nanmax(df_sd["rx_db"].to_numpy()))
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("p10", f"{p10:.1f} dB")
            c2.metric("p50", f"{p50:.1f} dB")
            c3.metric("p90", f"{p90:.1f} dB")
            c4.metric("max", f"{mx:.1f} dB")

# ---------------------------
# Debug tab
# ---------------------------
with tabs[2]:
    st.subheader("Debug")

    st.markdown("### Top sources (src)")
    if df.empty:
        st.info("Aucune donnée.")
    else:
        top_src = df["src"].value_counts().head(15).rename_axis("src").reset_index(name="count")
        st.dataframe(top_src, width="stretch", height=360)

    st.markdown("### Top iGates (igate)")
    if df.empty or "igate" not in df.columns:
        st.info("Aucune donnée / colonne 'igate' absente.")
    else:
        ig = df["igate"].replace("", np.nan).dropna()
        top_ig = ig.value_counts().head(15).rename_axis("igate").reset_index(name="count")
        st.dataframe(top_ig, width="stretch", height=360)

    with st.expander("Échantillon brut (raw)", expanded=False):
        if df.empty:
            st.write("—")
        else:
            st.dataframe(df[["ts_utc", "src", "dst", "igate", "raw"]].head(50), width="stretch", height=420)

    with st.expander("Infos pipeline", expanded=False):
        st.json(
            {
                "head": st.session_state.get("_ts", None),
                "rows_total_db": rows_total,
                "last_ts": last_ts,
                "since_iso": since_iso,
                "hours": hours,
                "dst_types": dst_types,
                "only_heard_by": only_heard_by,
                "igate_filter": igate_filter,
                "limit_rows": limit_rows,
                "basemap": basemap_label,
                "map_mode": map_mode,
                "show_rings": show_rings,
                "rings_km": rings_km,
                "df_loaded": int(len(df)),
                "df_has_latlon": int((df.get("lat", pd.Series(dtype=float)).notna() & df.get("lon", pd.Series(dtype=float)).notna()).sum()) if not df.empty else 0,
            }
        )
