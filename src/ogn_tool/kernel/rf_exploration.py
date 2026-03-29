from __future__ import annotations

from typing import Any, Dict

import logging
import re
import pandas as pd

from ogn_tool.kernel.directional_diagnostics import build_directional_diagnostics
from ogn_tool.kernel.network_timeseries import (
    compute_coverage_timeseries,
    compute_network_load_timeseries,
    compute_station_activity_timeseries,
)
from ogn_tool.kernel.rf_analysis_facade import (
    aggregate_signal_quality,
    build_rf_probability_grid,
    compute_network_blind_zones,
    evaluate_rf_diagnosis,
)
from ogn_tool.kernel.visibility_metrics import compute_visibility_metrics

logger = logging.getLogger(__name__)


def _as_frame(result: Any) -> pd.DataFrame:
    if isinstance(result, pd.DataFrame):
        return result.copy()

    if isinstance(result, dict):
        metrics = result.get("metrics") if isinstance(result.get("metrics"), dict) else {}
        rf_observations = metrics.get("rf_observations") if isinstance(metrics.get("rf_observations"), list) else []
        if rf_observations:
            rows = [row for row in rf_observations if isinstance(row, dict)]
            if rows:
                return pd.DataFrame(rows)

        positions = metrics.get("aircraft_positions") if isinstance(metrics.get("aircraft_positions"), list) else []
        if positions:
            rows: list[dict[str, Any]] = []
            for row in positions:
                if not isinstance(row, dict):
                    continue
                receivers = row.get("seen_by") if isinstance(row.get("seen_by"), list) else []
                first_station = receivers[0] if receivers else None
                rows.append(
                    {
                        "src": row.get("src") or row.get("aircraft_id"),
                        "igate": first_station,
                        "lat": row.get("lat"),
                        "lon": row.get("lon"),
                        "ts_epoch": row.get("timestamp_epoch") or row.get("timestamp"),
                        "seen_by": receivers,
                    }
                )
            return pd.DataFrame(rows)

    return pd.DataFrame()


def _to_jsonable(value: Any) -> Any:
    if isinstance(value, pd.DataFrame):
        return value.to_dict(orient="records")
    if isinstance(value, pd.Series):
        return value.to_dict()
    if isinstance(value, dict):
        return {k: _to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_jsonable(v) for v in value]
    return value


def _normalize_timestamp(value: Any) -> int | None:
    n = None
    try:
        n = float(value)
    except (TypeError, ValueError):
        return None
    if not pd.notna(n):
        return None
    # Normalize to epoch seconds
    if n > 1e12:
        n = n / 1000.0
    return int(n)




def _to_optional_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if pd.notna(number) else None


def _parse_aprs_raw(raw: str | None) -> dict[str, Any]:
    if not isinstance(raw, str):
        return {}

    out: dict[str, Any] = {}

    if raw.startswith('FLR') or ('>APRS' in raw and ' id' in raw):
        out['protocol'] = 'FLARM'
    elif 'FNT' in raw or 'FANET' in raw:
        out['protocol'] = 'FANET'
    else:
        out['protocol'] = None

    rssi_match = re.search(r'RSSI[:=](-?\d+(?:\.\d+)?)', raw)
    if rssi_match:
        out['rssi'] = _to_optional_float(rssi_match.group(1))

    snr_match = re.search(r'SNR[:=](-?\d+(?:\.\d+)?)', raw)
    if snr_match:
        out['snr'] = _to_optional_float(snr_match.group(1))

    return out


def _detect_protocol(row: dict[str, Any]) -> str | None:
    parsed = _parse_aprs_raw(row.get('raw'))
    if parsed.get('protocol'):
        return parsed['protocol']

    src = row.get('emitter_id') or row.get('src') or ''
    if isinstance(src, str):
        src_upper = src.upper()
        if src_upper.startswith('FLR') or src_upper.startswith('FLARM'):
            return 'FLARM'
        if src_upper.startswith('FNT') or src_upper.startswith('FANET'):
            return 'FANET'

    return None

def _normalize_message_rows(result: Any) -> list[dict[str, Any]]:
    frame = _as_frame(result)
    if frame.empty:
        return []

    rows: list[dict[str, Any]] = []
    for idx, row in frame.iterrows():
        emitter_lat = row.get("lat")
        emitter_lon = row.get("lon")
        if not (pd.notna(emitter_lat) and pd.notna(emitter_lon)):
            continue

        seen_by = row.get("seen_by")
        receivers = [str(v) for v in seen_by] if isinstance(seen_by, list) else []
        if not receivers:
            igate = row.get("igate")
            if isinstance(igate, str) and igate:
                receivers = [igate]

        parsed = _parse_aprs_raw(row.get("raw"))
        rssi = _to_optional_float(row.get("rssi"))
        snr = _to_optional_float(row.get("snr"))

        rows.append(
            {
                "message_id": str(row.get("id") or f"msg_{idx}"),
                "timestamp": _normalize_timestamp(row.get("ts_epoch")),
                "emitter_id": str(row.get("src") or "UNKNOWN"),
                "emitter_lat": float(emitter_lat),
                "emitter_lon": float(emitter_lon),
                "receivers": receivers,
                "rssi": rssi if rssi is not None else parsed.get("rssi"),
                "snr": snr if snr is not None else parsed.get("snr"),
                "raw": row.get("raw"),
                "protocol": _detect_protocol({
                    "raw": row.get("raw"),
                    "emitter_id": str(row.get("src") or "UNKNOWN"),
                }),
            }
        )
    return rows


# --- PUBLIC EXPLORATION API ---

def get_rf_field(result) -> Dict[str, Any]:
    if isinstance(result, dict):
        spatial = result.get("metrics", {}).get("spatial_network_features", {})
        coverage = spatial.get("coverage_density")
        if isinstance(coverage, list):
            return {"coverage_density": coverage}

    frame = _as_frame(result)
    if frame.empty:
        return {"coverage_density": []}
    return {"coverage_density": _to_jsonable(build_rf_probability_grid(frame))}


def get_blind_zones(result) -> Dict[str, Any]:
    if isinstance(result, dict):
        spatial = result.get("metrics", {}).get("spatial_network_features", {})
        for key in ("blind_problematic", "blind_actionable", "blind_zones_masked", "blind_zones"):
            values = spatial.get(key)
            if isinstance(values, list):
                return {"blind_zones": values, "source": key}

    frame = _as_frame(result)
    if frame.empty:
        return {"blind_zones": []}
    return {"blind_zones": _to_jsonable(compute_network_blind_zones(frame))}


def get_directional(result) -> Dict[str, Any]:
    if isinstance(result, dict):
        rf_analysis = result.get("intelligence", {}).get("rf_analysis")
        if isinstance(rf_analysis, dict):
            return _to_jsonable(rf_analysis)

    frame = _as_frame(result)
    if frame.empty:
        return {"azimuth_histogram": [], "directional_balance": {}, "shadow_map": []}

    diagnostics = build_directional_diagnostics(
        packets_rf=frame,
        packets_filtered=frame,
        station_lat=None,
        station_lon=None,
    )
    return _to_jsonable(diagnostics)


def get_visibility(result) -> Dict[str, Any]:
    frame = _as_frame(result)
    if frame.empty and isinstance(result, dict):
        spatial = result.get("metrics", {}).get("spatial_network_features", {})
        return {"summary": {"coverage_points": len(spatial.get("coverage_density") or [])}}

    metrics = compute_visibility_metrics(frame)
    return _to_jsonable(metrics)


def get_rf_quality(result) -> Dict[str, Any]:
    frame = _as_frame(result)
    if frame.empty:
        if isinstance(result, dict):
            signature = result.get("intelligence", {}).get("rf_analysis", {}).get("rf_signature")
            if isinstance(signature, dict):
                return {"rf_signature": signature}
        return {"quality": {}}

    return {"quality": _to_jsonable(aggregate_signal_quality(frame))}


def get_timeseries(result) -> Dict[str, Any]:
    frame = _as_frame(result)
    graph = {"observations": frame}
    return {
        "station_activity": _to_jsonable(compute_station_activity_timeseries(frame)),
        "network_load": _to_jsonable(compute_network_load_timeseries(frame)),
        "coverage": _to_jsonable(compute_coverage_timeseries(graph)),
    }


def get_diagnosis(result) -> Dict[str, Any]:
    if isinstance(result, dict):
        metrics = result.get("metrics", {})
        directional_balance = result.get("intelligence", {}).get("rf_analysis", {}).get("rf_signature", {})
        try:
            diagnosis = evaluate_rf_diagnosis(metrics, directional_balance)
            return {"diagnosis": _to_jsonable(diagnosis)}
        except Exception:
            decision = result.get("decision") if isinstance(result.get("decision"), dict) else {}
            return {"diagnosis": decision}

    return {"diagnosis": {}}


def get_messages(result: Any) -> Dict[str, Any]:
    normalized = _normalize_message_rows(result)
    if not normalized:
        return {"messages": []}

    station_map: dict[str, tuple[float, float]] = {}
    if isinstance(result, dict):
        stations = result.get("stations")
        if isinstance(stations, list):
            for s in stations:
                if not isinstance(s, dict):
                    continue
                sid = s.get("station_id")
                lat = s.get("lat")
                lon = s.get("lon")
                if isinstance(sid, str) and lat is not None and lon is not None:
                    station_map[sid] = (float(lat), float(lon))

    messages: list[dict[str, Any]] = []
    inferred_count = 0

    for row in normalized:
        emitter_lat = row["emitter_lat"]
        emitter_lon = row["emitter_lon"]

        for receiver_id in row.get("receivers", []):
            receiver_coords = station_map.get(receiver_id)
            receiver_is_inferred = receiver_coords is None
            if receiver_is_inferred:
                inferred_count += 1
                receiver_lat, receiver_lon = emitter_lat, emitter_lon
            else:
                receiver_lat, receiver_lon = receiver_coords

            messages.append(
                {
                    "message_id": row["message_id"],
                    "timestamp": row["timestamp"],
                    "emitter_id": row["emitter_id"],
                    "receiver_id": receiver_id,
                    "receiver_lat": receiver_lat,
                    "receiver_lon": receiver_lon,
                    "receiver_is_inferred": receiver_is_inferred,
                    "emitter_lat": emitter_lat,
                    "emitter_lon": emitter_lon,
                    "signal_strength": None,
                    "is_anomaly": None,
                }
            )

    logger.info("Stations available: %s", len(station_map))
    logger.info("Messages with inferred receiver position: %s", inferred_count)

    messages.sort(key=lambda m: (m.get("timestamp") is not None, m.get("timestamp") or 0), reverse=True)
    return {"messages": messages}



def get_messages_v2(result: Any) -> Dict[str, Any]:
    """
    Returns RF observations (v2 contract).

    One entry = one RF reception (emitter -> receiver).

    Notes:
    - observation_id is unique within a run (not globally stable).
    - Protocol, RSSI, and SNR are passed through when available.
    - Missing RF metadata remains null.
    """

    normalized = _normalize_message_rows(result)
    if not normalized:
        return {"messages": []}

    station_map: dict[str, tuple[float, float]] = {}

    if isinstance(result, dict):
        stations = result.get("stations")
        if isinstance(stations, list):
            for s in stations:
                if not isinstance(s, dict):
                    continue
                sid = s.get("station_id")
                lat = s.get("lat")
                lon = s.get("lon")
                if isinstance(sid, str) and lat is not None and lon is not None:
                    station_map[sid] = (float(lat), float(lon))

    messages_v2: list[dict[str, Any]] = []

    for row in normalized:
        emitter_lat = row["emitter_lat"]
        emitter_lon = row["emitter_lon"]

        for receiver_id in row.get("receivers", []):
            receiver_coords = station_map.get(receiver_id)

            receiver_is_inferred = receiver_coords is None

            if receiver_is_inferred:
                receiver_lat, receiver_lon = emitter_lat, emitter_lon
                receiver_source = "inferred"
            else:
                receiver_lat, receiver_lon = receiver_coords
                receiver_source = "observed"

            # Unique within a run for one emitter->receiver reception projection.
            observation_id = f"{row['message_id']}::{receiver_id}"

            protocol = row.get("protocol")
            rssi = _to_optional_float(row.get("rssi"))
            snr = _to_optional_float(row.get("snr"))

            messages_v2.append(
                {
                    "observation_id": observation_id,
                    "message_id": row["message_id"],  # legacy alias
                    "timestamp": row["timestamp"],  # epoch seconds UTC
                    "emitter": {
                        "id": row["emitter_id"],
                        "lat": emitter_lat,
                        "lon": emitter_lon,
                    },
                    "receiver": {
                        "id": receiver_id,
                        "lat": receiver_lat,
                        "lon": receiver_lon,
                        "source": receiver_source,
                    },
                    "transport": {
                        "protocol": protocol,
                        "network": "OGN",
                        "band": "868MHz" if protocol in ("FLARM", "FANET") else None,
                    },
                    "signal": {
                        "rssi": rssi,
                        "snr": snr,
                        "quality": None,
                    },
                    "meta": {
                        "is_relayed": False,
                        "hop_count": 1,
                    },
                }
            )

    messages_v2.sort(
        key=lambda m: (m.get("timestamp") is not None, m.get("timestamp") or 0),
        reverse=True,
    )

    logger.info("messages_v2 count: %s", len(messages_v2))

    return {"messages": messages_v2}
