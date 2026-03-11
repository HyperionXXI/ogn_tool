from __future__ import annotations

from typing import Dict, Iterable, List

import pandas as pd

from ogn_tool.analysis import rf_normalization
from ogn_tool.analysis.aircraft_states import extract_aircraft_states
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


def build_observations(packet_rows: Iterable[Dict]) -> List[RFObservationEvent]:
    """Convert packet rows to canonical RFObservationEvent objects.

    This analysis-layer function has no engine dependency and returns only
    model-level events for engine consumption.
    """
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


# Backward compatibility alias
build_observations_from_packets = build_observations


__all__ = ["build_observations", "build_observations_from_packets"]
