#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OGN / APRS-IS — Dashboard local (Courfaivre)

Objectifs (pragmatiques) :
- Lire la DB sqlite3 produite par collector.py (table packets)
- Explorer rapidement : trafic global, top sources, top iGates, et surtout "heard-by FK50887"
- Carte lisible SANS token Mapbox (CARTO basemap)
- Options de rendu (Points / Heatmap / Hexagones), basemap, opacité, taille
- Limiter CPU/RAM (fenêtre temporelle, max points, downsample)
"""

from __future__ import annotations

import os
import math
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, List, Any, Dict

import pandas as pd
import pydeck as pdk
import streamlit as st

APP_TITLE = "OGN / APRS-IS — Dashboard local (Courfaivre)"

# Basemaps (WebGL styles) — ne nécessitent pas de token Mapbox
CARTO_POSITRON = "https://basemaps.cartocdn.com/gl/positron-gl-style/style.json"
CARTO_DARK = "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
CARTO_VOYAGER = "https://basemaps.cartocdn.com/gl/voyager-gl-style/style.json"

DEFAULT_CENTER = (47.3358, 7.2730)  # Courfaivre approx
DEFAULT_RADIUS_KM = 200.0

# Regex fallback : paquets "heard-by" : "... ,qA?,FK50887:" (qAS / qAR / qAO / ...)
RE_QA_IGATE = re.compile(r",qA[A-Z0-9]{1,2},(?P<igate>[A-Z0-9\-]{3,12}):")


@dataclass(frozen=True)
class AppConfig:
    db_path: str
    center_lat: float
    center_lon: float


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(ts: str) -> datetime:
    # ts_utc est stocké en ISO avec timezone
    return datetime.fromisoformat(ts)


@st.cache_resource
def _db(db_path: str) -> sqlite3.Connection:
    # check_same_thread=False : Streamlit peut relancer dans un autre thread
    con = sqlite3.connect(db_path, check_same_thread=False)
    con.row_factory = sqlite3.Row
    return con


def _ensure_indexes(con: sqlite3.Connection) -> None:
    # Indexes utiles (vous les avez déjà, mais on garde ça "idempotent")
    con.execute("CREATE INDEX IF NOT EXISTS ix_packets_ts ON packets(ts_utc)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_packets_dst_ts ON packets(dst, ts_utc)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_packets_igate_ts ON packets(igate, ts_utc)")
    con.execute("CREATE INDEX IF NOT EXISTS ix_packets_src_ts ON packets(src, ts_utc)")
    con.commit()


@st.cache_data(ttl=2.0)
def _db_stats(db_path: str) -> Tuple[int, Optional[str]]:
    con = _db(db_path)
    row = con.execute("SELECT COUNT(*) AS c, MAX(ts_utc) AS last_ts FROM packets").fetchone()
    return int(row["c"]), row["last_ts"]


def _time_cut(hours: float) -> str:
    cut = _utc_now() - timedelta(hours=float(hours))
    return cut.isoformat()


def _parse_igate_fallback(raw: str) -> Optional[str]:
    m = RE_QA_IGATE.search(raw)
    if not m:
        return None
    return m.group("igate")


@st.cache_data(ttl=2.0, show_spinner=False)
def _query_points(
    db_path: str,
    hours: float,
    radius_km: float,
    center_lat: float,
    center_lon: float,
    max_points: int,
    only_types: Tuple[str, ...],
    igate_exact: str,
    coverage_fk50887_only: bool,
    debug_beacons_only: bool,
) -> pd.DataFrame:
    """
    Retourne un DataFrame de points (lat/lon) + métadonnées minimales.

    Note :
    - collector.py stocke : ts_utc, src, dst, igate, qas, lat, lon, raw
    - on filtre dans SQLite le plus possible
    """
    con = _db(db_path)
    cut = _time_cut(hours)

    # Filtrage base : fenêtre temporelle + positions valides + filtre r/ lat/lon/radius
    # Rayon : approx en degrés (suffisant pour du filtrage initial)
    # 1 deg lat ~ 111km ; lon dépend de cos(lat)
    deg_lat = radius_km / 111.0
    deg_lon = radius_km / (111.0 * max(0.2, abs(__import__("math").cos(__import__("math").radians(center_lat)))))

    where = [
        "ts_utc >= ?",
        "lat IS NOT NULL",
        "lon IS NOT NULL",
        "lat BETWEEN ? AND ?",
        "lon BETWEEN ? AND ?",
    ]
    params: List[object] = [cut, center_lat - deg_lat, center_lat + deg_lat, center_lon - deg_lon, center_lon + deg_lon]

    if only_types:
        # dst = "OGNFNT" / "OGFLR" / "OGADSB" / ...
        where.append("dst IN (%s)" % ",".join(["?"] * len(only_types)))
        params.extend(list(only_types))

    if igate_exact.strip():
        where.append("igate = ?")
        params.append(igate_exact.strip())

    if debug_beacons_only:
        # Ne montrer que les beacons de la station (src=FK50887)
        where.append("src = ?")
        params.append("FK50887")

    sql = f"""
        SELECT ts_utc, src, dst, igate, qas, lat, lon, raw
        FROM packets
        WHERE {' AND '.join(where)}
        ORDER BY ts_utc DESC
        LIMIT ?
    """
    params.append(int(max_points))

    df = pd.read_sql_query(sql, con, params=params)

    if df.empty:
        df["igate_eff"] = pd.Series(dtype=str)
        df["heard_by_fk50887"] = pd.Series(dtype=bool)
        return df

    # igate_eff = igate si présent, sinon parse fallback
    df["igate_eff"] = df["igate"].fillna("").astype(str)
    mask_missing = df["igate_eff"].str.len().eq(0)
    if mask_missing.any():
        df.loc[mask_missing, "igate_eff"] = df.loc[mask_missing, "raw"].map(lambda s: _parse_igate_fallback(str(s)) or "")

    # heard_by_fk50887 : paquets gated par FK50887 (igate_eff == FK50887)
    df["heard_by_fk50887"] = df["igate_eff"].eq("FK50887")

    if coverage_fk50887_only:
        # Garde uniquement les trames qui ont transité via FK50887.
        df = df[df["heard_by_fk50887"]].copy()

    return df


@st.cache_data(ttl=5.0, show_spinner=False)
def _top_counts(df: pd.DataFrame, col: str, n: int = 15) -> pd.DataFrame:
    if df.empty or col not in df.columns:
        return pd.DataFrame(columns=[col, "count"])
    out = df[col].fillna("").astype(str)
    out = out[out.str.len() > 0]
    vc = out.value_counts().head(n)
    return vc.rename_axis(col).reset_index(name="count")


def _metric_safe_int(x) -> int:
    try:
        return int(x)
    except Exception:
        return 0


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Great-circle distance (km)
    r = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def _build_deck(
    df: pd.DataFrame,
    *,
    map_style: str,
    view_state: Dict[str, Any],
    display_mode: str,
    point_size_px: int,
    point_opacity: float,
    hex_radius_m: int,
    heatmap_radius_px: int,
    show_station: bool,
    station_lat: float,
    station_lon: float,
) -> pdk.Deck:
    """Create a pydeck map.

    display_mode:
      - "Points": raw positions
      - "Hexagones (coverage)": density aggregation
      - "Heatmap": smoothed density
    """

    layers = []

    # Optional station marker (your groundstation location)
    if show_station:
        st_df = pd.DataFrame([{"lat": station_lat, "lon": station_lon, "name": "FK50887 (station)"}])
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=st_df,
                get_position="[lon, lat]",
                get_radius=10,  # px
                radius_units="pixels",
                get_fill_color=[0, 0, 0, 220],
                get_line_color=[255, 255, 255, 255],
                line_width_min_pixels=1,
                pickable=True,
            )
        )

    if df.empty:
        return pdk.Deck(layers=layers, initial_view_state=pdk.ViewState(**view_state), map_style=map_style)

    # Normalize / guard columns used by tooltips
    if "heard_by_fk50887" not in df.columns:
        df = df.assign(heard_by_fk50887=False)

    # Colors (kept simple, consistent)
    # - Heard-by FK50887: blue
    # - Others: red
    df = df.copy()
    df["__color"] = df["heard_by_fk50887"].apply(lambda x: [65, 145, 255, int(255 * point_opacity)] if bool(x) else [255, 90, 90, int(255 * point_opacity)])

    tooltip = {
        "html": (
            "<b>{src}</b> → <b>{dst}</b><br/>"
            "igate: {igate_eff}<br/>"
            "ts: {ts_utc}<br/>"
            "heard-by FK50887: {heard_by_fk50887}<br/>"
            "{dist_line}"
        ),
        "style": {"backgroundColor": "rgba(30,30,30,0.92)", "color": "white"},
    }

    # Pre-format optional distance line (if present)
    if "dist_km" in df.columns:
        df["dist_line"] = df["dist_km"].map(lambda x: f"dist: {x:.1f} km" if pd.notna(x) else "")
    else:
        df["dist_line"] = ""

    if display_mode == "Points":
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position="[lon, lat]",
                get_radius=point_size_px,
                radius_units="pixels",
                get_fill_color="__color",
                get_line_color=[255, 255, 255, 40],
                line_width_min_pixels=1,
                pickable=True,
                stroked=True,
            )
        )

    elif display_mode == "Heatmap":
        # HeatmapLayer ignores per-point colors; it uses density.
        layers.append(
            pdk.Layer(
                "HeatmapLayer",
                data=df,
                get_position="[lon, lat]",
                radius_pixels=heatmap_radius_px,
                intensity=1,
                threshold=0.05,
                pickable=False,
            )
        )
        # Add a small scatter overlay for "what's what" when zoomed in
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=df,
                get_position="[lon, lat]",
                get_radius=max(2, point_size_px // 2),
                radius_units="pixels",
                get_fill_color="__color",
                pickable=True,
                stroked=False,
            )
        )

    else:  # Hexagones
        layers.append(
            pdk.Layer(
                "HexagonLayer",
                data=df,
                get_position="[lon, lat]",
                radius=hex_radius_m,
                elevation_scale=1,
                elevation_range=[0, 800],
                extruded=False,  # keep 2D (more like gliderradar coverage)
                pickable=True,
                opacity=min(0.8, max(0.1, point_opacity)),
            )
        )
        # Add sparse points for context
        layers.append(
            pdk.Layer(
                "ScatterplotLayer",
                data=df.sample(min(len(df), 800), random_state=0) if len(df) > 800 else df,
                get_position="[lon, lat]",
                get_radius=max(2, point_size_px // 3),
                radius_units="pixels",
                get_fill_color="__color",
                pickable=False,
                stroked=False,
            )
        )

    return pdk.Deck(
        layers=layers,
        initial_view_state=pdk.ViewState(**view_state),
        map_style=map_style,
        tooltip=tooltip,
    )
def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    st.title(APP_TITLE)

    # Config via env, sinon defaults
    db_path = os.environ.get("OGN_DB", "ogn_log.sqlite3")
    center_lat = float(os.environ.get("OGN_CENTER_LAT", str(DEFAULT_CENTER[0])))
    center_lon = float(os.environ.get("OGN_CENTER_LON", str(DEFAULT_CENTER[1])))

    cfg = AppConfig(db_path=db_path, center_lat=center_lat, center_lon=center_lon)

    con = _db(cfg.db_path)
    _ensure_indexes(con)

    # Sidebar
    st.sidebar.header("Filtres")

    hours = st.sidebar.slider("Fenêtre d'analyse (heures)", min_value=0.5, max_value=48.0, value=6.0, step=0.5)
    radius_km = st.sidebar.slider("Rayon (km) — filtre r/..", min_value=10.0, max_value=500.0, value=DEFAULT_RADIUS_KM, step=10.0)

    types_all = ["OGNFNT", "OGFLR", "OGADSB", "OGNSKY", "OGNAVI", "APRS", "OGFLR7", "OGADSL"]
    types_sel = st.sidebar.multiselect("Types (dst)", options=types_all, default=["OGNFNT", "OGFLR"])

    max_points = st.sidebar.slider("Max points affichés (carte)", min_value=200, max_value=20000, value=4000, step=200)

    igate_exact = st.sidebar.text_input("iGate (callsign) — exact", value="")

    coverage_fk50887_only = st.sidebar.checkbox("Couverture: ne garder que les trames gated par FK50887", value=False)
    debug_beacons_only = st.sidebar.checkbox("Debug: ne montrer que les beacons (src=FK50887)", value=False)

    st.sidebar.divider()
    st.sidebar.subheader("Carte")
    basemap_name = st.sidebar.selectbox(
        "Fond de carte",
        ["CARTO Positron", "CARTO Voyager", "CARTO Dark"],
        index=0,
    )
    basemap_style = {"CARTO Positron": CARTO_POSITRON, "CARTO Voyager": CARTO_VOYAGER, "CARTO Dark": CARTO_DARK}[basemap_name]

    display_mode = st.sidebar.selectbox("Affichage", ["Points", "Hexagones (coverage)", "Heatmap"], index=0)

    st.sidebar.markdown("**Vue**")
    center_lat = st.sidebar.number_input("Centre lat", value=float(DEFAULT_CENTER[0]), format="%.6f")
    center_lon = st.sidebar.number_input("Centre lon", value=float(DEFAULT_CENTER[1]), format="%.6f")
    zoom = st.sidebar.slider("Zoom", min_value=6, max_value=15, value=11)
    pitch = st.sidebar.slider("Inclinaison (pitch)", min_value=0, max_value=60, value=0)

    show_station = st.sidebar.checkbox("Afficher la station (FK50887)", value=True)

    st.sidebar.markdown("**Style**")
    layer_opacity = st.sidebar.slider("Opacité", 0.05, 1.0, 0.55, 0.05)

    point_size_px = st.sidebar.slider("Taille points (px)", 2, 20, 6)
    heatmap_radius_px = st.sidebar.slider("Rayon heatmap (px)", 20, 250, 80, 5)
    hex_radius = st.sidebar.slider("Rayon hexagones (m)", 150, 4000, 900, 50)

# Header stats
    total_rows, last_ts = _db_stats(cfg.db_path)
    colA, colB, colC = st.columns([1.2, 1.2, 3.0])
    with colA:
        st.metric("Rows en DB (total)", f"{total_rows:,}".replace(",", "'"))
    with colB:
        st.metric("Dernier paquet (UTC)", last_ts or "—")
    with colC:
        # DB vivante si last_ts < 10s
        alive = False
        if last_ts:
            try:
                age_s = (_utc_now() - _parse_iso(last_ts)).total_seconds()
                alive = age_s < 10.0
            except Exception:
                alive = False
        st.success("DB vivante (paquets récents)" if alive else "DB non rafraîchie (ou pause collector)")

    # Data
    df = _query_points(
        db_path=cfg.db_path,
        hours=hours,
        radius_km=radius_km,
        center_lat=cfg.center_lat,
        center_lon=cfg.center_lon,
        max_points=max_points,
        only_types=tuple(types_sel),
        igate_exact=igate_exact,
        coverage_fk50887_only=coverage_fk50887_only,
        debug_beacons_only=debug_beacons_only,
    )
    # Optional per-point distance to the station (useful for quick coverage stats/tooltips)
    if not df.empty:
        df["dist_km"] = df.apply(lambda r: _haversine_km(cfg.center_lat, cfg.center_lon, float(r["lat"]), float(r["lon"])), axis=1)


    # Metrics window
    
    # Header stats
    st.markdown("## OGN / APRS-IS — Dashboard local (Courfaivre)")

    # Status: is DB being updated?
    now_utc = datetime.now(timezone.utc)
    last_ts = pd.to_datetime(last_packet_utc) if last_packet_utc else None
    is_fresh = False
    if last_ts is not None and pd.notna(last_ts):
        age_s = (now_utc - last_ts.to_pydatetime()).total_seconds()
        is_fresh = age_s <= 120  # 2 minutes
    status_txt = "DB vivante (paquets récents)" if is_fresh else "DB non rafraîchie (ou pause collector)"

    st.success(status_txt)

    # Metrics window
    m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
    with m1:
        st.metric("Rows en DB (total)", f"{total_rows:,}".replace(",", "'"))
    with m2:
        st.metric("Dernier paquet (UTC)", str(last_packet_utc)[:26] if last_packet_utc else "—")
    with m3:
        st.metric("Paquets dans la fenêtre", f"{packets_in_window:,}".replace(",", "'"))
    with m4:
        st.metric("Objets uniques (src)", f"{unique_src:,}".replace(",", "'"))
    with m5:
        st.metric("Points avec positions", f"{points_with_pos:,}".replace(",", "'"))

    # Distance stats (useful mainly when coverage filter is ON)
    df_dist = df[df["heard_by_fk50887"]] if (cov and "heard_by_fk50887" in df.columns) else df
    dist_max = float(df_dist["dist_km"].max()) if (not df_dist.empty and "dist_km" in df_dist.columns) else None
    dist_p95 = float(df_dist["dist_km"].quantile(0.95)) if (not df_dist.empty and "dist_km" in df_dist.columns) else None

    with m6:
        st.metric("Distance max (km)", f"{dist_max:.1f}" if dist_max is not None else "—")
    with m7:
        st.metric("Distance P95 (km)", f"{dist_p95:.1f}" if dist_p95 is not None else "—")

    st.markdown("### Carte")

    view_state = {"latitude": center_lat, "longitude": center_lon, "zoom": zoom, "pitch": pitch}

    if df.empty:
        st.info("Aucun point pour les filtres choisis.")
    else:
        deck = _build_deck(
            df,
            map_style=basemap_style,
            view_state=view_state,
            display_mode=display_mode,
            point_size_px=int(point_size_px),
            point_opacity=float(layer_opacity),
            hex_radius_m=int(hex_radius),
            heatmap_radius_px=int(heatmap_radius_px),
            show_station=bool(show_station),
            station_lat=float(cfg.center_lat),
            station_lon=float(cfg.center_lon),
        )
        st.pydeck_chart(deck, width="stretch")


    st.subheader("Top sources (src)")
    st.dataframe(_top_counts(df, "src", 20), width="stretch", hide_index=True)

    st.subheader("Top iGates (igate_eff)")
    st.dataframe(_top_counts(df, "igate_eff", 20), width="stretch", hide_index=True)

    with st.expander("Debug (10 raw lignes)"):
        if df.empty:
            st.write("—")
        else:
            for s in df["raw"].head(10).tolist():
                st.code(str(s)[:300], language="text")


if __name__ == "__main__":
    main()
