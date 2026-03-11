from __future__ import annotations

from typing import Dict, Iterable, List

import pandas as pd

from ogn_tool.analysis import rf_normalization
from ogn_tool.analysis.aircraft_states import extract_aircraft_states
from ogn_tool.analysis import signal_distance, azimuth, radio_horizon
from ogn_tool.models.rf_observation_vector import RFObservationVector
from ogn_tool.models.rf_types import RFObservationEvent, packet_to_rf_event, state_to_rf_event


def _to_frame(packet_rows: Iterable[Dict]) -> pd.DataFrame:
    if isinstance(packet_rows, pd.DataFrame):
        return packet_rows.copy()
    return pd.DataFrame(list(packet_rows))


def _normalize_packet_rows(packet_rows: Iterable[Dict]) -> pd.DataFrame:
    """Normalize packet rows before state/reception processing.

    Backward compatibility strategy:
    - preserve original columns
    - overlay normalized canonical + legacy aliases
    - fallback to original rows on errors
    """
    raw_df = _to_frame(packet_rows)
    if raw_df.empty:
        return pd.DataFrame()

    original_df = raw_df.copy()
    try:
        normalized_df = rf_normalization.normalize_packets(raw_df)
        required = set(rf_normalization.CANONICAL_COLUMNS)
        if not required.issubset(set(normalized_df.columns)):
            return original_df

        for col in rf_normalization.CANONICAL_COLUMNS + ["igate", "src", "ts_epoch"]:
            if col in normalized_df.columns:
                original_df[col] = normalized_df[col]

        return original_df
    except Exception:
        return original_df


def _coalesce(series: pd.Series) -> float | None:
    vals = pd.to_numeric(series, errors="coerce").dropna()
    if vals.empty:
        return None
    return float(vals.iloc[0])


def _extract_rf_receptions(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=list(rf_normalization.CANONICAL_COLUMNS) + ["igate", "src", "ts_epoch"])
    return rf_normalization.normalize_packets(df, keep_legacy_aliases=True)


def _compute_state_geometry(aircraft_states: pd.DataFrame, rf_receptions: pd.DataFrame) -> pd.DataFrame:
    if aircraft_states.empty:
        return pd.DataFrame(columns=["aircraft_id", "timestamp", "distance", "bearing", "altitude_difference"])

    geom_candidates = rf_receptions.copy()
    key_cols = ["aircraft_id", "timestamp"]
    grouped = (
        geom_candidates.groupby(key_cols, dropna=False)
        .agg(
            distance=("distance_km", _coalesce) if "distance_km" in geom_candidates.columns else ("timestamp", lambda _: None),
            bearing=("bearing_deg", _coalesce) if "bearing_deg" in geom_candidates.columns else ("timestamp", lambda _: None),
            altitude_difference=("relative_alt_m", _coalesce) if "relative_alt_m" in geom_candidates.columns else ("timestamp", lambda _: None),
        )
        .reset_index()
    )
    return grouped[["aircraft_id", "timestamp", "distance", "bearing", "altitude_difference"]]


def _expand_rf_receptions_with_states(
    rf_receptions: pd.DataFrame,
    aircraft_states: pd.DataFrame,
    state_geometry: pd.DataFrame,
) -> pd.DataFrame:
    if rf_receptions.empty:
        return pd.DataFrame()

    key_cols = ["aircraft_id", "timestamp"]
    states_min = (
        aircraft_states[["aircraft_id", "timestamp", "lat", "lon", "altitude"]].copy()
        if not aircraft_states.empty
        else pd.DataFrame(columns=["aircraft_id", "timestamp", "lat", "lon", "altitude"])
    )
    states_min = states_min.rename(columns={"lat": "state_lat", "lon": "state_lon", "altitude": "state_altitude"})

    out = rf_receptions.merge(states_min, on=key_cols, how="left")
    out = out.merge(state_geometry, on=key_cols, how="left")
    return out


def _build_rf_observations_frame(packet_rows: Iterable[Dict]) -> pd.DataFrame:
    normalized_df = _normalize_packet_rows(packet_rows)
    if normalized_df.empty:
        return pd.DataFrame()

    rf_receptions = _extract_rf_receptions(normalized_df)
    if rf_receptions.empty:
        return pd.DataFrame()

    aircraft_states = extract_aircraft_states(rf_receptions)
    state_geometry = _compute_state_geometry(aircraft_states, rf_receptions)
    expanded = _expand_rf_receptions_with_states(rf_receptions, aircraft_states, state_geometry)

    obs = pd.DataFrame(index=expanded.index)
    obs["station_id"] = expanded.get("station_id")
    obs["aircraft_id"] = expanded.get("aircraft_id")
    obs["timestamp"] = pd.to_numeric(expanded.get("timestamp"), errors="coerce").astype("Int64")
    obs["lat"] = pd.to_numeric(expanded.get("lat", expanded.get("state_lat")), errors="coerce")
    obs["lon"] = pd.to_numeric(expanded.get("lon", expanded.get("state_lon")), errors="coerce")
    obs["altitude"] = pd.to_numeric(expanded.get("altitude", expanded.get("state_altitude")), errors="coerce")

    obs["distance"] = pd.to_numeric(expanded.get("distance"), errors="coerce")
    obs["bearing"] = pd.to_numeric(expanded.get("bearing"), errors="coerce")
    obs["altitude_difference"] = pd.to_numeric(expanded.get("altitude_difference"), errors="coerce")

    obs["snr"] = pd.to_numeric(expanded.get("snr", expanded.get("snr_db")), errors="coerce")
    obs["freq_offset"] = pd.to_numeric(expanded.get("freq_offset"), errors="coerce")
    obs["bit_errors"] = pd.to_numeric(expanded.get("bit_errors"), errors="coerce").astype("Int64")

    obs["igate"] = expanded.get("igate", expanded.get("station_id"))
    obs["src"] = expanded.get("src", expanded.get("aircraft_id"))
    obs["ts_epoch"] = pd.to_numeric(expanded.get("ts_epoch", expanded.get("timestamp")), errors="coerce").astype("Int64")

    for col in ["_row_id", "raw", "qas", "dst", "ts_utc"]:
        if col in expanded.columns:
            obs[col] = expanded[col]

    return obs


def _as_float(value: object) -> float | None:
    num = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(num):
        return None
    return float(num)


def build_observation_vector(
    row: Dict,
    station_lat: float,
    station_lon: float,
    station_id: str | None = None,
    station_alt_m: float = 400.0,
) -> RFObservationVector | None:
    """Build RFObservationVector using signal_distance, azimuth and radio_horizon modules."""

    lat = _as_float(row.get("lat"))
    lon = _as_float(row.get("lon"))
    if lat is None or lon is None:
        return None

    aircraft_id = str(row.get("aircraft_id") or row.get("src") or "")
    st_id = str(station_id or row.get("station_id") or row.get("igate") or "")
    if not aircraft_id or not st_id:
        return None

    altitude_m = _as_float(row.get("altitude"))
    if altitude_m is None:
        altitude_m = _as_float(row.get("alt"))
    if altitude_m is None:
        altitude_m = _as_float(row.get("altitude_m"))
    if altitude_m is None:
        altitude_m = 0.0

    distance_km = _as_float(row.get("distance_km"))
    if distance_km is None:
        distance_km = _as_float(row.get("distance"))
    if distance_km is None:
        distance_km = float(
            signal_distance.haversine_km_vector(
                float(station_lat), float(station_lon), [float(lat)], [float(lon)]
            )[0]
        )

    bearing_deg = _as_float(row.get("bearing_deg"))
    if bearing_deg is None:
        bearing_deg = _as_float(row.get("bearing"))
    if bearing_deg is None:
        az_df = pd.DataFrame([
            {
                "lat": float(lat),
                "lon": float(lon),
                "distance_km": float(distance_km),
            }
        ])
        az_stats = azimuth.compute_azimuth_radiation(az_df, float(station_lat), float(station_lon))
        if az_stats is not None and not az_stats.empty and "az_bin" in az_stats.columns:
            bearing_deg = float(az_stats.iloc[0]["az_bin"])
        else:
            bearing_deg = 0.0

    raw = row.get("raw")
    if raw is None:
        altitude_ft = int(max(0.0, float(altitude_m)) / 0.3048)
        raw = f"A={altitude_ft:06d}"

    rh_input = pd.DataFrame([
        {
            "raw": raw,
            "lat": float(lat),
            "lon": float(lon),
        }
    ])
    rh = radio_horizon.analyze(
        df_observations=rh_input,
        station_lat=float(station_lat),
        station_lon=float(station_lon),
        station_alt_m=float(station_alt_m),
    )
    radio_horizon_km = None
    if isinstance(rh, dict):
        summary = rh.get("summary") or {}
        radio_horizon_km = _as_float(summary.get("horizon_mean_km"))
    if radio_horizon_km is None:
        radio_horizon_km = float(3.57 * ((max(float(station_alt_m), 0.0) ** 0.5) + (max(float(altitude_m), 0.0) ** 0.5)))

    terrain_blocked = row.get("terrain_blocked")
    if terrain_blocked is not None:
        terrain_blocked = bool(terrain_blocked)

    return RFObservationVector(
        station_id=st_id,
        aircraft_id=aircraft_id,
        lat=float(lat),
        lon=float(lon),
        altitude_m=float(altitude_m),
        distance_km=float(distance_km),
        bearing_deg=float(bearing_deg),
        radio_horizon_km=float(radio_horizon_km),
        terrain_blocked=terrain_blocked,
    )


def build_observations(packet_rows: Iterable[Dict]) -> List[RFObservationVector]:
    """Convert packet rows to RFObservationVector objects (new default contract)."""
    obs_df = _build_rf_observations_frame(packet_rows)

    if obs_df is None or obs_df.empty:
        rows = _normalize_packet_rows(packet_rows)
        vectors: List[RFObservationVector] = []
        for row in rows.to_dict("records"):
            vector = build_observation_vector(
                row,
                station_lat=_as_float(row.get("station_lat")) or 0.0,
                station_lon=_as_float(row.get("station_lon")) or 0.0,
                station_id=str(row.get("station_id") or row.get("igate") or ""),
            )
            if vector is not None:
                vectors.append(vector)
        return vectors

    vectors: List[RFObservationVector] = []
    for row in obs_df.to_dict("records"):
        vector = build_observation_vector(
            row,
            station_lat=_as_float(row.get("station_lat")) or _as_float(row.get("lat")) or 0.0,
            station_lon=_as_float(row.get("station_lon")) or _as_float(row.get("lon")) or 0.0,
            station_id=str(row.get("station_id") or row.get("igate") or ""),
        )
        if vector is not None:
            vectors.append(vector)

    return vectors


def build_observations_events(packet_rows: Iterable[Dict]) -> List[RFObservationEvent]:
    """Compatibility adapter returning legacy RFObservationEvent objects."""
    obs_df = _build_rf_observations_frame(packet_rows)

    if obs_df is None or obs_df.empty:
        rows = _normalize_packet_rows(packet_rows)
        return [packet_to_rf_event(row) for row in rows.to_dict("records")]

    observations: List[RFObservationEvent] = []
    for row in obs_df.to_dict("records"):
        event = state_to_rf_event(row, row)
        event.distance = _as_float(row.get("distance"))
        event.bearing = _as_float(row.get("bearing"))
        event.altitude_difference = _as_float(row.get("altitude_difference"))
        event.snr = _as_float(row.get("snr"))
        event.freq_offset = _as_float(row.get("freq_offset"))
        event.bit_errors = (
            int(float(row.get("bit_errors")))
            if row.get("bit_errors") is not None and pd.notna(row.get("bit_errors"))
            else None
        )
        event.metadata = {**(event.metadata or {}), "_row_id": row.get("_row_id")}
        observations.append(event)

    return observations


# Backward compatibility aliases
build_observations_from_packets = build_observations
build_observations_from_packets_events = build_observations_events


__all__ = [
    "build_observations",
    "build_observations_events",
    "build_observations_from_packets",
    "build_observations_from_packets_events",
    "build_observation_vector",
]
