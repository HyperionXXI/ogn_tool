#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OGN / APRS-IS — Dashboard local (Courfaivre)

Focus:
- Coverage "heard-by FK50887" lisible: points colorés par distance + anneaux + hull (optionnel)
- Basemaps sans token (CARTO)
- Refresh stable (auto-refresh optionnel)
- Performance: fenêtre temporelle + limite points + cache TTL
"""

from __future__ import annotations

import os
import re
import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, List

import pandas as pd
import pydeck as pdk
import streamlit as st

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None


APP_TITLE = "OGN / APRS-IS — Dashboard local"

# Basemaps (WebGL styles) — pas besoin de token Mapbox
CARTO_POSITRON = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
CARTO_DARK = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
CARTO_VOYAGER = "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json"

BASEMAPS = {
    "CARTO Positron (clair)": CARTO_POSITRON,
    "CARTO Voyager (mix)": CARTO_VOYAGER,
    "CARTO Dark Matter (sombre)": CARTO_DARK,
}

# Station (par défaut tes coords; surcharge possible via env)
DEFAULT_STATION_CALL = os.getenv("OGN_STATION", "FK50887").strip() or "FK50887"
DEFAULT_STATION_LAT = float(os.getenv("OGN_STATION_LAT", "47.33583"))
DEFAULT_STATION_LON = float(os.getenv("OGN_STATION_LON", "7.273"))

DEFAULT_DB = os.getenv("OGN_DB", "ogn_log.sqlite3")

# Regex "heard-by" dans raw: "... ,qA?,FK50887:" (qAS / qAR / qAO / ...)
RE_QA_IGATE = re.compile(r",qA[A-Z0-9]{1,2},(?P<igate>[A-Z0-9\-]{3,12}):")


@dataclass(frozen=True)
class AppConfig:
    db_path: str
    station_call: str
    station_lat: float
    station_lon: float


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def haversine_km(lat0: float, lon0: float, lat: float, lon: float) -> float:
    # WGS84 approx
    r = 6371.0
    p0 = math.radians(lat0)
    p1 = math.radians(lat)
    dphi = math.radians(lat - lat0)
    dl = math.radians(lon - lon0)
    a = math.sin(dphi / 2) ** 2 + math.cos(p0) * math.cos(p1) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def haversine_vec_km(lat0: float, lon0: float, lats, lons):
    # vectorisé simple sans numpy obligatoire
    out = []
    for la, lo in zip(lats, lons):
        out.append(haversine_km(lat0, lon0, float(la), float(lo)))
    return out


def parse_igate_fallback(raw: str) -> Optional[str]:
    m = RE_QA_IGATE.search(raw or "")
    if not m:
        return None
    return m.group("igate")


def circle_polygon(lat0: float, lon0: float, radius_km: float, n: int = 96) -> List[List[float]]:
    """
    Retourne un polygone [lon, lat] approximant un cercle (géodésique simplifié).
    Suffisant pour une visualisation.
    """
    coords = []
    # conversion radiale approx
    # 1 deg lat ≈ 111 km ; lon ≈ 111*cos(lat)
    deg_lat = radius_km / 111.0
    deg_lon = radius_km / (111.0 * max(0.2, abs(math.cos(math.radians(lat0)))))

    for i in range(n):
        ang = 2 * math.pi * (i / n)
        lat = lat0 + deg_lat * math.sin(ang)
        lon = lon0 + deg_lon * math.cos(ang)
        coords.append([lon, lat])
    coords.append(coords[0])
    return coords


def convex_hull(points_xy: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    Monotonic chain convex hull.
    points_xy: list of (x,y) unique-ish.
    returns hull in CCW order (last not repeated).
    """
    pts = sorted(set(points_xy))
    if len(pts) <= 2:
        return pts

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower = []
    for p in pts:
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)

    upper = []
    for p in reversed(pts):
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)

    return lower[:-1] + upper[:-1]


@st.cache_resource
def db_conn(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(db_path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def ensure_indexes(con: sqlite3.Connection) -> None:
    con.execute("CREATE INDEX IF NOT EXISTS ix_packets_ts ON packets(ts_utc)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_packets_dst_ts ON packets(dst, ts_utc)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_packets_igate_ts ON packets(igate, ts_utc)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_packets_src_ts ON packets(src, ts_utc)")
    con.commit()


@st.cache_data(ttl=2.0)
def get_db_status(db_path: str):
    con = db_conn(db_path)
    row = con.execute("SELECT COUNT(*) AS c, MAX(ts_utc) AS last_ts FROM packets").fetchone()
    last_ts = row["last_ts"]
    last_dt = datetime.fromisoformat(last_ts) if last_ts else None
    return int(row["c"]), last_dt


def time_cut(hours: float) -> str:
    return (utc_now() - timedelta(hours=float(hours))).isoformat()


@st.cache_data(ttl=2.0, show_spinner=False)
def load_points(
    db_path: str,
    tick: int,
    hours: float,
    dst_filter: Tuple[str, ...],
    igate_filter: str,
    limit_rows: int,
) -> pd.DataFrame:
    """
    tick est volontairement un paramètre: il casse le cache lors de l'auto-refresh.
    """
    con = db_conn(db_path)
    cut = time_cut(hours)

    where = ["ts_utc >= ?", "lat IS NOT NULL", "lon IS NOT NULL"]
    params: List[object] = [cut]

    if dst_filter:
        where.append("dst IN (%s)" % ",".join(["?"] * len(dst_filter)))
        params.extend(list(dst_filter))

    if igate_filter.strip():
        where.append("igate = ?")
        params.append(igate_filter.strip())

    sql = f"""
        SELECT ts_utc, src, dst, igate, qas, lat, lon, raw
        FROM packets
        WHERE {' AND '.join(where)}
        ORDER BY ts_utc DESC
        LIMIT ?
    """
    params.append(int(limit_rows))
    df = pd.read_sql_query(sql, con, params=params)
    return df


def add_effective_igate(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        df["igate_eff"] = pd.Series(dtype=str)
        return df
    df = df.copy()
    df["igate_eff"] = df["igate"].fillna("").astype(str)
    m = df["igate_eff"].str.len().eq(0)
    if m.any():
        df.loc[m, "igate_eff"] = df.loc[m, "raw"].map(lambda s: parse_igate_fallback(str(s)) or "")
    return df


def color_by_distance_km(d: float) -> List[int]:
    """
    Retourne [r,g,b,a] en fonction de la distance.
    Simple et lisible:
      proche = vert, moyen = jaune/orange, loin = rouge.
    """
    # clamp
    x = max(0.0, min(120.0, float(d)))
    if x <= 20:
        # vert -> jaune
        t = x / 20.0
        r = int(40 + 180 * t)
        g = int(220)
        b = int(60)
    elif x <= 60:
        # jaune -> orange
        t = (x - 20.0) / 40.0
        r = int(220)
        g = int(220 - 90 * t)
        b = int(60)
    else:
        # orange -> rouge
        t = (x - 60.0) / 60.0
        r = int(220)
        g = int(130 - 110 * t)
        b = int(60 - 40 * t)
    a = 160
    return [r, g, b, a]


def main():
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)

    cfg = AppConfig(
        db_path=DEFAULT_DB,
        station_call=DEFAULT_STATION_CALL,
        station_lat=DEFAULT_STATION_LAT,
        station_lon=DEFAULT_STATION_LON,
    )

    # Sidebar
    st.sidebar.header("Paramètres")

    db_path = st.sidebar.text_input("DB SQLite", value=cfg.db_path)
    station_call = st.sidebar.text_input("Station callsign", value=cfg.station_call)
    station_lat = st.sidebar.number_input("Station lat", value=float(cfg.station_lat), format="%.6f")
    station_lon = st.sidebar.number_input("Station lon", value=float(cfg.station_lon), format="%.6f")

    basemap_name = st.sidebar.selectbox("Fond de carte", list(BASEMAPS.keys()), index=0)
    map_style = BASEMAPS[basemap_name]

    hours = st.sidebar.slider("Fenêtre temporelle (heures)", min_value=0.5, max_value=48.0, value=6.0, step=0.5)

    dst_opts = ["OGNFNT", "OGFLR", "OGFLR7", "OGADSB", "OGADSL", "OGNSKY", "OGNAVI", "OGNDVS", "APRS"]
    dst_filter = st.sidebar.multiselect("Types (dst)", options=dst_opts, default=["OGNFNT", "OGFLR", "OGFLR7"])
    igate_filter = st.sidebar.text_input("Filtre igate (optionnel)", value="")

    only_heard_by = st.sidebar.checkbox(
        f"Coverage: uniquement 'heard-by {station_call}'",
        value=True,
    )

    show_rings = st.sidebar.checkbox("Afficher anneaux de portée", value=True)
    rings_km = st.sidebar.multiselect("Anneaux (km)", options=[5, 10, 15, 20, 25, 30, 50, 75, 100, 150, 200], default=[10, 25, 50, 100])

    show_hull = st.sidebar.checkbox("Afficher hull (enveloppe) des points coverage", value=False)

    view_mode = st.sidebar.selectbox(
        "Mode carte",
        ["Points (couleur = distance)", "Heatmap (densité)", "Hexagon (densité)"],
        index=0,
    )

    point_radius_m = st.sidebar.slider("Taille points (m)", min_value=30, max_value=400, value=120, step=10)
    max_points = st.sidebar.slider("Max points affichés", min_value=200, max_value=20000, value=5000, step=200)

    auto_refresh = st.sidebar.checkbox("Auto-refresh (5s)", value=False)
    if auto_refresh and st_autorefresh is not None:
        tick = st_autorefresh(interval=5_000, key="tick")
    else:
        # tick stable => cache TTL agit
        tick = int(st.session_state.get("manual_tick", 0))

    if st.sidebar.button("Refresh maintenant"):
        st.session_state["manual_tick"] = int(st.session_state.get("manual_tick", 0)) + 1
        st.rerun()

    # DB status
    try:
        con = db_conn(db_path)
        ensure_indexes(con)
        total_rows, last_dt = get_db_status(db_path)
    except Exception as e:
        st.error(f"Impossible d'ouvrir la DB: {e}")
        st.stop()

    c1, c2, c3 = st.columns([1, 2, 2])
    c1.metric("Rows DB", f"{total_rows:,}")
    c2.metric("Dernier paquet (UTC)", str(last_dt) if last_dt else "—")
    if last_dt:
        age_s = (utc_now() - last_dt).total_seconds()
        if age_s > 15:
            c3.warning(f"DB potentiellement figée (dernier paquet il y a {age_s:.0f}s)")
        else:
            c3.success("DB vivante")

    # Load data
    limit_rows = min(int(max_points * 3), 200_000)  # garde-fou
    df = load_points(
        db_path=db_path,
        tick=int(tick),
        hours=float(hours),
        dst_filter=tuple(dst_filter),
        igate_filter=igate_filter,
        limit_rows=limit_rows,
    )
    df = add_effective_igate(df)

    if df.empty:
        st.warning("Aucun paquet dans la fenêtre/filtre courant.")
        # carte quand même: station + anneaux éventuels
        df_map = pd.DataFrame([], columns=["lat", "lon"])
    else:
        df = df.dropna(subset=["lat", "lon"]).copy()
        # Recent first
        df = df.sort_values("ts_utc", ascending=False)

        if only_heard_by:
            ig = df["igate_eff"].fillna("")
            mask_igate = (ig == station_call)

            raw = df["raw"].fillna("")
            # forme robuste: ",qA?,FK50887:"
            mask_raw = raw.str.contains(rf",qA[A-Z0-9]{{1,2}},{re.escape(station_call)}:", regex=True)

            df = df[mask_igate | mask_raw].copy()

        df_map = df.head(int(max_points)).copy()

    # Metrics coverage
    if not df_map.empty:
        dists = haversine_vec_km(station_lat, station_lon, df_map["lat"].tolist(), df_map["lon"].tolist())
        df_map["distance_km"] = dists
        df_map["color"] = df_map["distance_km"].map(color_by_distance_km)
        max_d = float(df_map["distance_km"].max())
        p95 = float(pd.Series(dists).quantile(0.95))
    else:
        max_d = 0.0
        p95 = 0.0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Paquets (fenêtre)", f"{len(df):,}" if not df.empty else "0")
    m2.metric("Points affichés", f"{len(df_map):,}")
    m3.metric("Distance max (km)", f"{max_d:.1f}" if max_d else "—")
    m4.metric("Distance P95 (km)", f"{p95:.1f}" if p95 else "—")

    # Map layers
    st.subheader("Carte")

    station_df = pd.DataFrame([{"lat": station_lat, "lon": station_lon, "label": station_call}])

    layers = []

    # Rings
    if show_rings and rings_km:
        ring_polys = []
        for rk in sorted(set(int(x) for x in rings_km)):
            ring_polys.append(
                {
                    "name": f"{rk} km",
                    "polygon": circle_polygon(station_lat, station_lon, float(rk), n=96),
                }
            )
        layers.append(
            pdk.Layer(
                "PolygonLayer",
                data=ring_polys,
                get_polygon="polygon",
                get_fill_color=[0, 0, 0, 0],
                get_line_color=[60, 120, 220, 140],
                line_width_min_pixels=1,
                pickable=True,
            )
        )

    # Hull
    if show_hull and not df_map.empty and len(df_map) >= 6:
        # projection equirectangulaire locale autour station
        lat0 = math.radians(station_lat)
        pts_xy = []
        for la, lo in zip(df_map["lat"].tolist(), df_map["lon"].tolist()):
            x = (math.radians(float(lo)) - math.radians(station_lon)) * math.cos(lat0)
            y = (math.radians(float(la)) - math.radians(station_lat))
            pts_xy.append((x, y))
        hull = convex_hull(pts_xy)
        if len(hull) >= 3:
            poly = []
            for x, y in hull:
                lo = station_lon + math.degrees(x / max(1e-9, math.cos(lat0)))
                la = station_lat + math.degrees(y)
                poly.append([lo, la])
            poly.append(poly[0])
            hull_df = pd.DataFrame([{"polygon": poly, "name": "Hull coverage"}])
            layers.append(
                pdk.Layer(
                    "PolygonLayer",
                    data=hull_df,
                    get_polygon="polygon",
                    get_fill_color=[255, 140, 0, 35],
                    get_line_color=[255, 140, 0, 160],
                    line_width_min_pixels=2,
                    pickable=True,
                )
            )

    # Main layer
    if not df_map.empty:
        if view_mode.startswith("Heatmap"):
            layers.append(
                pdk.Layer(
                    "HeatmapLayer",
                    data=df_map,
                    get_position="[lon, lat]",
                    opacity=0.85,
                    radiusPixels=45,
                )
            )
        elif view_mode.startswith("Hexagon"):
            layers.append(
                pdk.Layer(
                    "HexagonLayer",
                    data=df_map,
                    get_position="[lon, lat]",
                    radius=1200,
                    elevation_scale=10,
                    elevation_range=[0, 1000],
                    pickable=True,
                    extruded=False,
                )
            )
        else:
            layers.append(
                pdk.Layer(
                    "ScatterplotLayer",
                    data=df_map,
                    get_position="[lon, lat]",
                    get_radius=point_radius_m,
                    get_fill_color="color",
                    pickable=True,
                )
            )

    # Station marker (toujours)
    layers.append(
        pdk.Layer(
            "ScatterplotLayer",
            data=station_df,
            get_position="[lon, lat]",
            get_radius=250,
            get_fill_color=[20, 20, 20, 220],
            pickable=True,
        )
    )

    # View
    zoom = 9 if max_d <= 60 else 8
    view_state = pdk.ViewState(latitude=station_lat, longitude=station_lon, zoom=zoom, pitch=0)

    tooltip = {
        "text": (
            "src: {src}\n"
            "dst: {dst}\n"
            "igate: {igate_eff}\n"
            "dist_km: {distance_km}\n"
            "ts: {ts_utc}"
        )
    }

    deck = pdk.Deck(
        layers=layers,
        initial_view_state=view_state,
        map_style=map_style,
        tooltip=tooltip,
    )

    st.pydeck_chart(deck, height=520, width="stretch")

    # Tables / debug
    with st.expander("Top sources / iGates / Debug"):
        if not df.empty:
            st.write("Top sources (src)")
            top_src = df["src"].value_counts().head(20).rename_axis("src").reset_index(name="count")
            st.dataframe(top_src, width="stretch", height=260)

            st.write("Top iGates (igate_eff)")
            ig = df["igate_eff"].replace("", pd.NA).dropna()
            top_ig = ig.value_counts().head(20).rename_axis("igate").reset_index(name="count")
            st.dataframe(top_ig, width="stretch", height=260)

            st.write("10 lignes récentes (après filtres)")
            cols = ["ts_utc", "src", "dst", "igate", "igate_eff", "lat", "lon", "raw"]
            st.dataframe(df_map[cols].head(10), width="stretch")


if __name__ == "__main__":
    main()