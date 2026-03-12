from __future__ import annotations

import pandas as pd


def detect_blind_zones(coverage_grid: pd.DataFrame) -> pd.DataFrame:
    if coverage_grid is None or coverage_grid.empty:
        return pd.DataFrame(columns=["grid_lat", "grid_lon"])
    candidates = coverage_grid.copy()
    count_col = None
    for col in ["stations", "station_count", "observations", "packets"]:
        if col in candidates.columns:
            count_col = col
            break
    if count_col is None:
        return pd.DataFrame(columns=candidates.columns)
    return candidates[pd.to_numeric(candidates[count_col], errors="coerce").fillna(0) <= 1].copy()


def suggest_station_locations(graph: dict, coverage_grid: pd.DataFrame) -> list[dict]:
    blind = detect_blind_zones(coverage_grid)
    if blind.empty:
        return []
    out = []
    blind_count = float((((graph or {}).get("metrics") or {}).get("blind_zones") or {}).get("count", 0))
    for row in blind.to_dict("records"):
        lat = row.get("grid_lat", row.get("lat"))
        lon = row.get("grid_lon", row.get("lon"))
        if lat is None or lon is None:
            continue
        out.append({"lat": lat, "lon": lon, "score": blind_count + 1.0})
    out.sort(key=lambda item: item["score"], reverse=True)
    dedup = []
    seen = set()
    for item in out:
        key = (round(float(item["lat"]), 5), round(float(item["lon"]), 5))
        if key in seen:
            continue
        seen.add(key)
        dedup.append(item)
    return dedup


__all__ = ["detect_blind_zones", "suggest_station_locations"]
